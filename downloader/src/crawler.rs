use chrono::{FixedOffset, Utc};
use data_structures::metadata;
use feed_rs::parser;
use html_escape::decode_html_entities;
use reqwest_middleware::ClientWithMiddleware;
use std::{collections::HashMap, vec};
use tracing::warn;
use url::{ParseError, Url};
// time zones
// +08:00
pub static BEIJING_OFFSET: Option<FixedOffset> = FixedOffset::east_opt(8 * 60 * 60);

pub async fn crawl_link_page<'a>(
    url: &str,
    theme: &str,
    css_rule: &serde_yaml::Value,
    client: &ClientWithMiddleware,
) -> Result<HashMap<&'a str, Vec<String>>, Box<dyn std::error::Error>> {
    if css_rule.is_mapping() {
        let theme_rule = match css_rule.get(theme) {
            Some(s) => s,
            None => panic!("`{theme}` field not found in css_rule"),
        };
        let html = client.get(url).send().await?.text().await?;
        let document = nipper::Document::from(&html);
        // 返回结果init
        let mut result: HashMap<&str, Vec<String>> = HashMap::new();
        for rule in ["author", "link", "avatar"] {
            let fields = theme_rule
                .get(rule)
                .ok_or(format!("`{theme}-{rule}` 字段缺失"))?;
            let fields = fields
                .as_sequence()
                .ok_or(format!("`{theme}-{rule}` 字段格式错误"))?;

            let mut res = vec![];
            for field in fields {
                let match_rule: &str = field
                    .get("selector")
                    .ok_or(format!("`{theme}-{rule}-selector` 字段缺失"))?
                    .as_str()
                    .ok_or(format!("`{theme}-{rule}-selector` 字段格式错误"))?;
                let attr = field
                    .get("attr")
                    .ok_or(format!("`{theme}-{rule}-attr` 字段缺失"))?
                    .as_str()
                    .ok_or(format!("`{theme}-{rule}-attr` 字段格式错误"))?;

                for elem in document.select(match_rule).iter() {
                    let parsed_field = match attr {
                        "text" => elem.text().to_string(),
                        _ => match elem.attr(attr).map(|r| r.to_string()) {
                            Some(v) => v,
                            None => continue,
                        },
                    };
                    // 解码 HTML 实体（如 &quot; &amp; 等）
                    let decoded_field = decode_html_entities(&parsed_field).to_string();
                    res.push(decoded_field);
                }
                // 当前规则获取到结果，则认为规则是有效的，短路后续规则
                if !res.is_empty() {
                    break;
                }
            }

            // info!("{:?}",html);

            result.insert(rule, res);
        }
        // DEBUG:
        // if result.len() < 4 {
        //     debug!(
        //         "页面：{}, 使用规则：{:?}, 解析结果：{:#?}",
        //         url, theme, result
        //     );
        // }
        Ok(result)
    } else {
        panic!("css_rule 格式错误");
    }
}

pub async fn crawl_post_page<'a>(
    url: &str,
    css_rules: &serde_yaml::Mapping,
    client: &ClientWithMiddleware,
) -> Result<HashMap<&'a str, Vec<String>>, Box<dyn std::error::Error>> {
    // let html = reqwest::get(url).await?.text().await?;
    // DEBUG:
    // debug!("{}", url);
    let html = client
        .get(url)
        .send()
        .await?
        .error_for_status()?
        .text()
        .await?;
    let document = nipper::Document::from(&html);
    // 返回结果init
    let mut result: HashMap<&str, Vec<String>> = HashMap::new();
    // 使用过的css规则
    let mut used_css_rules = vec![];
    'outer: for css_rule in css_rules {
        let use_theme = css_rule
            .0
            .as_str()
            .ok_or("无法解析字段，需要一个字符串".to_string())?;
        used_css_rules.push(use_theme.to_string());
        for current_field in ["title", "link", "created", "updated"] {
            let fields = css_rule
                .1
                .get(current_field)
                .ok_or(format!("`{use_theme}-{current_field}` 字段缺失"))?;
            let fields = fields
                .as_sequence()
                .ok_or(format!("`{use_theme}-{current_field}` 字段格式错误"))?;

            for field in fields {
                let match_rule: &str = field
                    .get("selector")
                    .ok_or(format!("`{use_theme}-{current_field}-selector` 字段缺失"))?
                    .as_str()
                    .ok_or(format!(
                        "`{use_theme}-{current_field}-selector` 字段格式错误"
                    ))?;
                let attr = field
                    .get("attr")
                    .ok_or(format!("`{use_theme}-{current_field}-attr` 字段缺失"))?
                    .as_str()
                    .ok_or(format!("`{use_theme}-{current_field}-attr` 字段格式错误"))?;

                let mut res = vec![];
                for elem in document.select(match_rule).iter() {
                    let parsed_field = match attr {
                        "text" => elem.text().to_string(),
                        _ => match elem.attr(attr).map(|r| r.to_string()) {
                            Some(v) => v,
                            None => continue,
                        },
                    };
                    // 解码 HTML 实体（如 &quot; &amp; 等）
                    let decoded_field = decode_html_entities(&parsed_field).to_string();
                    res.push(decoded_field);
                }
                if !res.is_empty() {
                    // DEBUG:
                    // debug!("{}-{}-{}-{}", use_theme, match_rule, attr, current_field);
                    if !result.contains_key(current_field) {
                        result.insert(current_field, res);
                    }
                    // 全部字段解析完毕
                    if result.len() == 4 {
                        break 'outer;
                    }
                } else {
                    // DEBUG:
                    // debug!(
                    //     "页面：{},字段：{},使用规则:{},解析结果：{:?}",
                    //     url, current_field, use_theme, res
                    // );
                };
            }
        }
    }
    // DEBUG:
    // if result.len() < 4 {
    //     debug!(
    //         "页面：{}, 已使用规则：{:?}, 解析结果：{:?}",
    //         url, used_css_rules, result
    //     );
    // }
    result.insert("rules", used_css_rules);
    Ok(result)
}

pub async fn crawl_post_page_feed(
    url: &str,
    base_url: &Url,
    client: &ClientWithMiddleware,
) -> Result<Vec<metadata::BasePosts>, Box<dyn std::error::Error>> {
    // DEBUG:
    // debug!("feed.....{}", url);
    let html = client
        .get(url)
        .send()
        .await?
        .error_for_status()?
        .bytes()
        .await?;
    // let html = reqwest::get(url).await?.bytes().await?;
    if let Ok(feed_from_xml) = parser::parse(html.as_ref()) {
        let entries = feed_from_xml.entries;
        // 返回结果init
        let mut format_base_posts = vec![];
        for entry in entries {
            // 标题
            let title = entry.title.map_or(String::from("文章标题获取失败"), |t| {
                // 解码 HTML 实体
                decode_html_entities(&t.content).to_string()
            });
            // url链接
            let link = if !entry.links.is_empty() {
                entry.links[0].href.clone()
            } else {
                warn!("feed无法解析url链接");
                continue;
            };
            // 处理相对地址
            let link = match Url::parse(&link) {
                Ok(_) => link,
                Err(parse_error) => match parse_error {
                    ParseError::RelativeUrlWithoutBase => match base_url.join(&link) {
                        Ok(completion_url) => completion_url.to_string(),
                        Err(e) => {
                            warn!("无法拼接相对地址：{},error:{}", link, e);
                            continue;
                        }
                    },
                    _ => {
                        warn!("无法处理地址：{}", link);
                        continue;
                    }
                },
            };
            // 时间
            let created = match entry.published {
                Some(t) => tools::strptime_to_string_ymd(t.fixed_offset()),
                // 使用当前时间
                None => tools::strptime_to_string_ymd(
                    Utc::now().with_timezone(&BEIJING_OFFSET.unwrap()),
                ),
            };

            let updated = match entry.updated {
                Some(t) => tools::strptime_to_string_ymd(t.fixed_offset()),
                // 使用创建时间
                None => created.clone(),
            };
            let base_post =
                metadata::BasePosts::new(title, created, updated, link, "feed".to_string());
            format_base_posts.push(base_post);
        }
        Ok(format_base_posts)
    } else {
        Ok(Vec::new())
    }
}
