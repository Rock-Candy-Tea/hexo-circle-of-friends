use super::crawler;
use chrono::Utc;
use data_structures::{
    config::Settings,
    metadata::{self, BasePosts},
};
use regex::Regex;
use reqwest::{ClientBuilder as CL, Proxy};
use reqwest_middleware::{ClientBuilder, ClientWithMiddleware};
use reqwest_retry::{RetryTransientMiddleware, policies::ExponentialBackoff};
use std::collections::HashMap;
use std::time::Duration;
use tokio::{self, task::JoinSet};
use tools;
use tracing::{error, info, trace, warn};
use url::{ParseError, Url};

async fn get_joinset_result(
    joinset: &mut JoinSet<Vec<BasePosts>>,
    base_url: &Url,
) -> Result<Vec<BasePosts>, Box<dyn std::error::Error>> {
    while let Some(res) = joinset.join_next().await {
        if let Ok(success) = res
            && !success.is_empty()
        {
            info!("{} 解析成功! 共{}条", base_url, success.len());
            return Ok(success);
        }
    }
    Err("css request failed".into())
}

/// 构建请求客户端
pub fn build_client() -> ClientWithMiddleware {
    let timeout = Duration::new(20, 0);
    let baseclient = CL::new()
        .timeout(timeout)
        .use_rustls_tls()
        .danger_accept_invalid_certs(true);

    let baseclient = match tools::get_env_var("PROXY") {
        Ok(proxy) => {
            info!("use proxy: {}", proxy);
            baseclient.proxy(Proxy::all(proxy).unwrap())
        }
        Err(_) => baseclient,
    };
    let baseclient = baseclient.build().unwrap();
    let retry_policy = ExponentialBackoff::builder().build_with_max_retries(3);
    ClientBuilder::new(baseclient)
        .with(RetryTransientMiddleware::new_with_policy(retry_policy))
        .build()
}

/// 检查link页面解析结果的长度
/// 如果字段`author`、`link`、`avatar`缺失，则返回0
/// 否则，检查`author`和`link`的长度：
/// - 是否为0：若有一个为0，返回0
/// - 二者长度是否相等，如果不等，返回0，如果相等返回该长度
fn check_linkpage_res_length(download_res: &HashMap<&str, Vec<String>>) -> usize {
    if !download_res.contains_key("author")
        || !download_res.contains_key("link")
        || !download_res.contains_key("avatar")
    {
        warn!("字段`author`或字段`link`或字段`avatar`缺失，请检查css规则");
        return 0;
    }
    let author_field = download_res.get("author").unwrap();
    let link_field = download_res.get("link").unwrap();
    if author_field.is_empty() || link_field.is_empty() {
        0
    } else if author_field.len() != link_field.len() {
        warn!(
            "字段`author`长度: {}, 字段`link`长度: {},不一致，请检查css规则",
            author_field.len(),
            link_field.len()
        );
        0
    } else {
        author_field.len()
    }
}

/// 检查屏蔽url，匹配返回true，反之为false
fn check_block_site(block_sites: &Vec<String>, url: &str) -> bool {
    for pattern in block_sites {
        let re = Regex::new(pattern).unwrap();
        if re.is_match(url) {
            return true;
        }
    }
    false
}

pub async fn start_crawl_postpages(
    base_postpage_url: String,
    settings: &Settings,
    extra_feed_suffix: String,
    css_rules: &tools::Value,
    client: &ClientWithMiddleware,
) -> Result<Vec<metadata::BasePosts>, Box<dyn std::error::Error>> {
    // check block url
    let block_sites = &settings.block_site;
    if check_block_site(block_sites, &base_postpage_url) {
        return Ok(Vec::new());
    };
    let base_url = match Url::parse(&base_postpage_url) {
        Ok(v) => v,
        Err(e) => {
            error!("postpage_url:{} 解析失败:{}", base_postpage_url, e);
            return Ok(Vec::new());
        }
    };
    let css_rules = css_rules.clone();
    let mut joinset = JoinSet::new();

    if css_rules["post_page_rules"].is_mapping() {
        let css_rules = css_rules
            .get("post_page_rules")
            .unwrap()
            .as_mapping()
            .unwrap();
        let css_rules = css_rules.clone();
        let client_: ClientWithMiddleware = client.clone();
        let base_url_ = base_url.clone();

        for feed_suffix in [
            "atom.xml",
            "feed/atom",
            "rss.xml",
            "rss2.xml",
            "feed",
            "index.xml",
            extra_feed_suffix.as_str(),
        ] {
            let client = client.clone();
            let base_url = base_url.clone();
            let feed_url = base_url.join(feed_suffix)?;
            joinset.spawn(async move {
                match crawler::crawl_post_page_feed(feed_url.as_str(), &base_url, &client).await {
                    Ok(v) => v,
                    Err(e) => {
                        trace!("{}", e);
                        Vec::new()
                    }
                }
            });
        }

        if let Ok(posts) = get_joinset_result(&mut joinset, &base_url).await {
            info!("使用feed规则解析成功:{}", base_url);
            return Ok(posts);
        }
        joinset.spawn(async move {
            // 获取当前时间
            let mut download_postpage_res =
                match crawler::crawl_post_page(&base_postpage_url, &css_rules, &client_).await {
                    Ok(v) => v,
                    Err(e) => {
                        warn!("{}", e);
                        return Vec::new();
                    }
                };
            let length;
            // 字段缺失检查

            if download_postpage_res.contains_key("title")
                && download_postpage_res.contains_key("link")
            {
                if download_postpage_res.get("title").unwrap().len()
                    != download_postpage_res.get("link").unwrap().len()
                {
                    error!(
                        "url: {} 解析结果缺失`title`或`link`长度不等",
                        base_postpage_url
                    );
                    return Vec::new();
                } else {
                    // 关键字段长度相等
                    length = download_postpage_res.get("title").unwrap().len()
                }
            } else if download_postpage_res.contains_key("link") {
                warn!("url: {} 解析结果缺失`title`", base_postpage_url);
                // 补充对应长度的title
                length = download_postpage_res.get("link").unwrap().len();
                let title = vec![String::from("文章标题获取失败"); length];
                download_postpage_res.insert("title", title);
            } else {
                // 缺失link，无力回天
                error!("url: {} 解析结果缺失`link`", base_postpage_url);
                return Vec::new();
            }

            let mut format_base_posts = vec![];
            for i in 0..length {
                let mut title = download_postpage_res.get("title").unwrap()[i]
                    .trim()
                    .to_string();
                if title.is_empty() {
                    title = String::from("文章标题获取失败")
                };
                let link = download_postpage_res.get("link").unwrap()[i]
                    .trim()
                    .to_string();
                // 处理相对地址
                let link = match Url::parse(&link) {
                    Ok(_) => link,
                    Err(parse_error) => match parse_error {
                        ParseError::RelativeUrlWithoutBase => match base_url_.join(&link) {
                            Ok(completion_url) => completion_url.to_string(),
                            Err(e) => {
                                warn!("无法拼接相对地址：{},error：{}", link, e);
                                continue;
                            }
                        },
                        _ => {
                            warn!("无法处理地址：{}", link);
                            continue;
                        }
                    },
                };
                let created = match download_postpage_res.get("created") {
                    Some(v) => {
                        if i < v.len() {
                            // 如果有值，则使用该值
                            tools::strftime_to_string_ymd(v[i].trim())
                        } else {
                            // 否则使用当前时间
                            tools::strptime_to_string_ymd(
                                Utc::now().with_timezone(&crawler::BEIJING_OFFSET.unwrap()),
                            )
                        }
                    }
                    // 缺失created字段，否则使用当前时间
                    None => tools::strptime_to_string_ymd(
                        Utc::now().with_timezone(&crawler::BEIJING_OFFSET.unwrap()),
                    ),
                };
                let updated = match download_postpage_res.get("updated") {
                    Some(v) => {
                        if i < v.len() {
                            // 如果有值，则使用该值
                            tools::strftime_to_string_ymd(v[i].trim())
                        } else {
                            // 否则使用created
                            created.clone()
                        }
                    }
                    // 否则使用created
                    None => created.clone(),
                };
                let rules = download_postpage_res.get("rules").unwrap();
                let base_post =
                    metadata::BasePosts::new(title, created, updated, link, rules.join(","));
                format_base_posts.push(base_post);
            }
            format_base_posts
        });
        if let Ok(posts) = get_joinset_result(&mut joinset, &base_url).await {
            info!("使用css规则解析成功:{}", base_url);
            Ok(posts)
        } else {
            info!("解析失败:{}", base_url);
            Ok(Vec::new())
        }
    } else {
        error!("css_rule 格式错误");
        panic!("css_rule 格式错误");
    }
}

pub async fn start_crawl_linkpages(
    settings: &Settings,
    css_rules: &tools::Value,
    client: &ClientWithMiddleware,
) -> Vec<metadata::Friends> {
    let mut format_base_friends = vec![];
    let start_urls = &settings.link;
    for linkmeta in start_urls {
        // check block url
        let block_sites = &settings.block_site;
        if check_block_site(block_sites, &linkmeta.link) {
            continue;
        };
        let download_linkpage_res = match crawler::crawl_link_page(
            &linkmeta.link,
            &linkmeta.theme,
            &css_rules["link_page_rules"],
            client,
        )
        .await
        {
            Ok(v) => v,
            Err(err) => {
                error!("linkpage:{} 解析失败:{}", linkmeta.link, err);
                continue;
            }
        };
        let length = check_linkpage_res_length(&download_linkpage_res);
        for i in 0..length {
            let author = download_linkpage_res.get("author").unwrap()[i]
                .trim()
                .to_string();
            // TODO 链接拼接检查
            let link = download_linkpage_res.get("link").unwrap()[i]
                .trim()
                .to_string();
            // TODO 链接拼接检查
            let _avatar = download_linkpage_res.get("avatar").unwrap();
            let avatar = if i < _avatar.len() {
                download_linkpage_res.get("avatar").unwrap()[i]
                    .trim()
                    .to_string()
            } else {
                // 默认图片
                String::from("https://sdn.geekzu.org/avatar/57d8260dfb55501c37dde588e7c3852c")
            };
            let tm = Utc::now().with_timezone(&crawler::BEIJING_OFFSET.unwrap());
            let created_at = tools::strptime_to_string_ymdhms(tm);
            let base_post = metadata::Friends::new(author, link, avatar, false, created_at);
            format_base_friends.push(base_post);
        }
    }
    format_base_friends
}
