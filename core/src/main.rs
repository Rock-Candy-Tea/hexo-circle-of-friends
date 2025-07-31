use std::fs::File;

use chrono::Utc;
use data_structures::metadata::{self, ArticleSummary};
use data_structures::response::AllPostData;
use db::{SqlitePool, mongo, mysql, sqlite};
use downloader::{download, genai::EnhancedSummaryProvider};
use tokio::{self};
use tracing::{error, info};

/// 极简模式，写入data.json文件
pub async fn write_data_to_json(pool: &SqlitePool) -> Result<(), Box<dyn std::error::Error>> {
    let posts = sqlite::select_all_from_posts(pool, 0, 0, "updated").await?;

    let last_updated_time = sqlite::select_latest_time_from_posts(pool).await?;

    let friends = sqlite::select_all_from_friends(pool).await?;
    let friends_num = friends.len();
    let mut active_num = 0;
    let mut lost_num = 0;
    for friend in friends {
        if friend.error {
            lost_num += 1;
        } else {
            active_num += 1;
        }
    }
    let data = AllPostData::new(
        friends_num,
        active_num,
        lost_num,
        posts.len(),
        last_updated_time,
        posts,
        0,
    );

    // 创建data.json文件并写入数据
    let file = File::create("data.json")?;
    serde_json::to_writer_pretty(file, &data)?;
    info!("数据已成功写入到data.json文件");

    Ok(())
}

/// 检查摘要是否需要更新
fn should_update_summary(
    existing_summary: &ArticleSummary,
    current_hash: &str,
) -> (bool, &'static str) {
    let content_unchanged = existing_summary.content_hash == current_hash;
    let summary_empty = existing_summary.summary.trim().is_empty();

    if content_unchanged && !summary_empty {
        (false, "内容未变化且摘要存在")
    } else if summary_empty {
        (true, "摘要为空")
    } else {
        (true, "内容已变化")
    }
}

/// 为文章生成摘要
async fn generate_article_summaries(
    fc_settings: &data_structures::config::Settings,
    client: &reqwest_middleware::ClientWithMiddleware,
) -> Result<(), Box<dyn std::error::Error>> {
    if !fc_settings.generate_summary.enabled {
        return Ok(());
    }

    // 创建增强摘要提供商并验证配置
    let summary_provider = EnhancedSummaryProvider::new(fc_settings.generate_summary.clone());
    if let Err(e) = summary_provider.validate_config() {
        error!("摘要生成配置无效: {}", e);
        return Err(e.into());
    }

    // 创建专用的LLM客户端（30秒超时）
    let llm_client = download::build_client(30, 0);

    info!(
        "开始生成文章摘要，使用提供商: {}",
        fc_settings.generate_summary.provider
    );
    info!(
        "配置参数 - 最大并发: {}, 等待限速: {}, 最大字符: {}",
        fc_settings.generate_summary.get_max_concurrent(),
        fc_settings.generate_summary.get_wait_on_rate_limit(),
        fc_settings.generate_summary.get_max_chars(),
    );

    match fc_settings.database.as_str() {
        "sqlite" => {
            let dbpool = sqlite::connect_sqlite_dbpool("data.db").await?;
            let posts = sqlite::select_all_from_posts(&dbpool, 0, 0, "updated").await?;

            for post in posts {
                let link = &post.meta.link;

                // 检查是否已经有缓存的摘要
                if let Ok(Some(existing_summary)) =
                    sqlite::select_article_summary_by_link(link, &dbpool).await
                {
                    // 获取当前文章的HTML内容
                    match download::start_crawl_detailpages(link, client).await {
                        Ok(html_content) => {
                            let current_hash = tools::calculate_content_hash(&html_content);

                            // 检查是否需要更新摘要
                            let (should_update, reason) =
                                should_update_summary(&existing_summary, &current_hash);
                            if !should_update {
                                info!("文章 {} {}，跳过摘要生成", link, reason);
                                continue;
                            }

                            info!("文章 {} {}，需要生成摘要", link, reason);

                            // 生成新的摘要
                            match summary_provider
                                .generate_summary(&llm_client, &html_content)
                                .await
                            {
                                Ok(summary_result) => {
                                    let now = tools::strptime_to_string_ymdhms(
                                        Utc::now()
                                            .with_timezone(&downloader::BEIJING_OFFSET.unwrap()),
                                    );
                                    let article_summary = ArticleSummary::new(
                                        link.clone(),
                                        current_hash,
                                        summary_result.summary,
                                        Some(summary_result.model),
                                        existing_summary.created_at,
                                        now,
                                    );

                                    if let Err(e) =
                                        sqlite::insert_article_summary(&article_summary, &dbpool)
                                            .await
                                    {
                                        error!("保存文章摘要失败 {}: {}", link, e);
                                    } else {
                                        info!("成功更新文章摘要: {}", link);
                                    }
                                }
                                Err(e) => {
                                    error!("生成文章摘要失败 {}: {}", link, e);
                                }
                            }
                        }
                        Err(e) => {
                            error!("获取文章详情失败 {}: {}", link, e);
                        }
                    }
                } else {
                    // 没有缓存的摘要，需要生成新的
                    info!("文章 {} 没有缓存摘要，需要生成新摘要", link);
                    match download::start_crawl_detailpages(link, client).await {
                        Ok(html_content) => {
                            let current_hash = tools::calculate_content_hash(&html_content);

                            match summary_provider
                                .generate_summary(&llm_client, &html_content)
                                .await
                            {
                                Ok(summary_result) => {
                                    let now = tools::strptime_to_string_ymdhms(
                                        Utc::now()
                                            .with_timezone(&downloader::BEIJING_OFFSET.unwrap()),
                                    );
                                    let article_summary = ArticleSummary::new(
                                        link.clone(),
                                        current_hash,
                                        summary_result.summary,
                                        Some(summary_result.model),
                                        now.clone(),
                                        now,
                                    );

                                    if let Err(e) =
                                        sqlite::insert_article_summary(&article_summary, &dbpool)
                                            .await
                                    {
                                        error!("保存文章摘要失败 {}: {}", link, e);
                                    } else {
                                        info!("成功生成文章摘要: {}", link);
                                    }
                                }
                                Err(e) => {
                                    error!("生成文章摘要失败 {}: {}", link, e);
                                }
                            }
                        }
                        Err(e) => {
                            error!("获取文章详情失败 {}: {}", link, e);
                        }
                    }
                }
            }
        }
        "mysql" => {
            let mysqlconnstr = tools::get_env_var("MYSQL_URI")?;
            let dbpool = mysql::connect_mysql_dbpool(&mysqlconnstr).await?;
            let posts = mysql::select_all_from_posts(&dbpool, 0, 0, "updated").await?;

            for post in posts {
                let link = &post.meta.link;

                if let Ok(Some(existing_summary)) =
                    mysql::select_article_summary_by_link(link, &dbpool).await
                {
                    match download::start_crawl_detailpages(link, client).await {
                        Ok(html_content) => {
                            let current_hash = tools::calculate_content_hash(&html_content);

                            // 检查是否需要更新摘要：
                            // 1. 哈希值不同（内容变化）
                            // 2. 摘要为空
                            let content_unchanged = existing_summary.content_hash == current_hash;
                            let summary_empty = existing_summary.summary.trim().is_empty();

                            if content_unchanged && !summary_empty {
                                info!("文章 {} 内容未变化且摘要存在，跳过摘要生成", link);
                                continue;
                            }

                            if summary_empty {
                                info!("文章 {} 摘要为空，需要生成摘要", link);
                            } else {
                                info!("文章 {} 内容已变化，需要更新摘要", link);
                            }

                            match summary_provider
                                .generate_summary(&llm_client, &html_content)
                                .await
                            {
                                Ok(summary_result) => {
                                    let now = tools::strptime_to_string_ymdhms(
                                        Utc::now()
                                            .with_timezone(&downloader::BEIJING_OFFSET.unwrap()),
                                    );
                                    let article_summary = ArticleSummary::new(
                                        link.clone(),
                                        current_hash,
                                        summary_result.summary,
                                        Some(summary_result.model),
                                        existing_summary.created_at,
                                        now,
                                    );

                                    if let Err(e) =
                                        mysql::insert_article_summary(&article_summary, &dbpool)
                                            .await
                                    {
                                        error!("保存文章摘要失败 {}: {}", link, e);
                                    } else {
                                        info!("成功更新文章摘要: {}", link);
                                    }
                                }
                                Err(e) => {
                                    error!("生成文章摘要失败 {}: {}", link, e);
                                }
                            }
                        }
                        Err(e) => {
                            error!("获取文章详情失败 {}: {}", link, e);
                        }
                    }
                } else {
                    match download::start_crawl_detailpages(link, client).await {
                        Ok(html_content) => {
                            let current_hash = tools::calculate_content_hash(&html_content);

                            match summary_provider
                                .generate_summary(&llm_client, &html_content)
                                .await
                            {
                                Ok(summary_result) => {
                                    let now = tools::strptime_to_string_ymdhms(
                                        Utc::now()
                                            .with_timezone(&downloader::BEIJING_OFFSET.unwrap()),
                                    );
                                    let article_summary = ArticleSummary::new(
                                        link.clone(),
                                        current_hash,
                                        summary_result.summary,
                                        Some(summary_result.model),
                                        now.clone(),
                                        now,
                                    );

                                    if let Err(e) =
                                        mysql::insert_article_summary(&article_summary, &dbpool)
                                            .await
                                    {
                                        error!("保存文章摘要失败 {}: {}", link, e);
                                    } else {
                                        info!("成功生成文章摘要: {}", link);
                                    }
                                }
                                Err(e) => {
                                    error!("生成文章摘要失败 {}: {}", link, e);
                                }
                            }
                        }
                        Err(e) => {
                            error!("获取文章详情失败 {}: {}", link, e);
                        }
                    }
                }
            }
        }
        "mongodb" => {
            let mongodburi = tools::get_env_var("MONGODB_URI")?;
            let clientdb = mongo::connect_mongodb_clientdb(&mongodburi).await?;
            let posts = mongo::select_all_from_posts(&clientdb, 0, 0, "updated").await?;

            for post in posts {
                let link = &post.meta.link;

                if let Ok(Some(existing_summary)) =
                    mongo::select_article_summary_by_link(link, &clientdb).await
                {
                    match download::start_crawl_detailpages(link, client).await {
                        Ok(html_content) => {
                            let current_hash = tools::calculate_content_hash(&html_content);

                            // 检查是否需要更新摘要：
                            // 1. 哈希值不同（内容变化）
                            // 2. 摘要为空
                            let content_unchanged = existing_summary.content_hash == current_hash;
                            let summary_empty = existing_summary.summary.trim().is_empty();

                            if content_unchanged && !summary_empty {
                                info!("文章 {} 内容未变化且摘要存在，跳过摘要生成", link);
                                continue;
                            }

                            if summary_empty {
                                info!("文章 {} 摘要为空，需要生成摘要", link);
                            } else {
                                info!("文章 {} 内容已变化，需要更新摘要", link);
                            }

                            match summary_provider
                                .generate_summary(&llm_client, &html_content)
                                .await
                            {
                                Ok(summary_result) => {
                                    let now = tools::strptime_to_string_ymdhms(
                                        Utc::now()
                                            .with_timezone(&downloader::BEIJING_OFFSET.unwrap()),
                                    );
                                    let article_summary = ArticleSummary::new(
                                        link.clone(),
                                        current_hash,
                                        summary_result.summary,
                                        Some(summary_result.model),
                                        existing_summary.created_at,
                                        now,
                                    );

                                    if let Err(e) =
                                        mongo::insert_article_summary(&article_summary, &clientdb)
                                            .await
                                    {
                                        error!("保存文章摘要失败 {}: {}", link, e);
                                    } else {
                                        info!("成功更新文章摘要: {}", link);
                                    }
                                }
                                Err(e) => {
                                    error!("生成文章摘要失败 {}: {}", link, e);
                                }
                            }
                        }
                        Err(e) => {
                            error!("获取文章详情失败 {}: {}", link, e);
                        }
                    }
                } else {
                    match download::start_crawl_detailpages(link, client).await {
                        Ok(html_content) => {
                            let current_hash = tools::calculate_content_hash(&html_content);

                            match summary_provider
                                .generate_summary(&llm_client, &html_content)
                                .await
                            {
                                Ok(summary_result) => {
                                    let now = tools::strptime_to_string_ymdhms(
                                        Utc::now()
                                            .with_timezone(&downloader::BEIJING_OFFSET.unwrap()),
                                    );
                                    let article_summary = ArticleSummary::new(
                                        link.clone(),
                                        current_hash,
                                        summary_result.summary,
                                        Some(summary_result.model),
                                        now.clone(),
                                        now,
                                    );

                                    if let Err(e) =
                                        mongo::insert_article_summary(&article_summary, &clientdb)
                                            .await
                                    {
                                        error!("保存文章摘要失败 {}: {}", link, e);
                                    } else {
                                        info!("成功生成文章摘要: {}", link);
                                    }
                                }
                                Err(e) => {
                                    error!("生成文章摘要失败 {}: {}", link, e);
                                }
                            }
                        }
                        Err(e) => {
                            error!("获取文章详情失败 {}: {}", link, e);
                        }
                    }
                }
            }
        }
        _ => return Err("不支持的数据库类型".into()),
    }

    info!("文章摘要生成完成");
    Ok(())
}

#[tokio::main]
async fn main() {
    let _guard = tools::init_tracing(
        "fcircle_core",
        Some(
            "error,fcircle_core=debug,db=debug,downloader=debug,tools=debug,data_structures=debug",
        ),
    );

    let now = Utc::now().with_timezone(&downloader::BEIJING_OFFSET.unwrap());

    let css_rules: tools::Value = tools::get_yaml("./css_rules.yaml").unwrap();
    let fc_settings = tools::get_yaml_settings("./fc_settings.yaml").unwrap();

    let client = download::build_client(10, 3);

    // let _cssrule = css_rules.clone();
    let format_base_friends =
        download::start_crawl_linkpages(&fc_settings, &css_rules, &client).await;
    // info!("{:?}", format_base_friends);
    let mut all_res = vec![];
    let mut tasks = vec![];

    for friend in format_base_friends {
        // if friend.link != "https://akilar.top/" {
        //     continue;
        // }
        let fc_settings = fc_settings.clone();
        let client = client.clone();
        let css_rules = css_rules.clone();
        let task = tokio::spawn(async move {
            let format_base_posts = download::start_crawl_postpages(
                friend.link.clone(),
                &fc_settings,
                "".to_string(),
                &css_rules,
                &client,
            )
            .await
            .unwrap();
            // info!("{:?}",format_base_posts);
            (friend, format_base_posts)
        });
        tasks.push(task);
    }

    // 处理配置项友链
    if fc_settings.settings_friends_links.enable {
        info!("处理配置项友链...");
        let json_friends_links = if !fc_settings
            .settings_friends_links
            .json_api_or_path
            .is_empty()
        {
            if fc_settings
                .settings_friends_links
                .json_api_or_path
                .starts_with("http")
            {
                if let Ok(json_friends_links) = download::start_get_friends_links_from_json(
                    &fc_settings.settings_friends_links.json_api_or_path,
                    &client,
                )
                .await
                {
                    info!(
                        "从api:{}获取配置项友链成功",
                        fc_settings.settings_friends_links.json_api_or_path
                    );
                    json_friends_links.friends
                } else {
                    error!(
                        "从api:{}获取配置项友链失败",
                        fc_settings.settings_friends_links.json_api_or_path
                    );
                    Vec::new()
                }
            } else if let Ok(json_friends_links) =
                tools::get_json_friends_links(&fc_settings.settings_friends_links.json_api_or_path)
            {
                info!(
                    "从文件:{}获取配置项友链成功",
                    fc_settings.settings_friends_links.json_api_or_path
                );
                json_friends_links.friends
            } else {
                error!(
                    "从文件:{}获取配置项友链失败",
                    fc_settings.settings_friends_links.json_api_or_path
                );
                Vec::new()
            }
        } else {
            Vec::new()
        };
        // concat json_friends_links and settings_friend_postpages
        let mut settings_friend_postpages = fc_settings.settings_friends_links.list.clone();
        settings_friend_postpages.extend(json_friends_links);
        // info!("settings_friend_postpages: {:?}", settings_friend_postpages);
        for postpage_vec in settings_friend_postpages {
            let tm: chrono::DateTime<chrono::FixedOffset> = now;
            let created_at = tools::strptime_to_string_ymdhms(tm);
            let base_post = metadata::Friends::new(
                postpage_vec[0].clone(),
                postpage_vec[1].clone(),
                postpage_vec[2].clone(),
                false,
                created_at,
            );
            // 请求主页面
            let fc_settings = fc_settings.clone();
            let client = client.clone();
            let css_rules = css_rules.clone();
            let task = tokio::spawn(async move {
                let format_base_posts = match download::start_crawl_postpages(
                    base_post.link.clone(),
                    &fc_settings,
                    if postpage_vec.len() == 3 {
                        String::from("")
                    } else if postpage_vec.len() == 4 {
                        postpage_vec[3].clone()
                    } else {
                        panic!("`SETTINGS_FRIENDS_LINKS-list`下的数组长度只能为3或4");
                    },
                    &css_rules,
                    &client,
                )
                .await
                {
                    Ok(v) => v,
                    Err(e) => {
                        error!("{}", e);
                        return (base_post, vec![]);
                    }
                };
                // info!("{:?}",format_base_posts);
                (base_post, format_base_posts)
            });
            tasks.push(task);
        }
    }
    for task in tasks {
        let mut res = task.await.unwrap();
        if fc_settings.max_posts_num > 0 {
            res.1 = res
                .1
                .iter()
                .take(fc_settings.max_posts_num)
                .cloned()
                .collect();
        }
        all_res.push(res);
    }
    let mut success_posts = Vec::new();
    let mut success_friends = Vec::new();
    let mut failed_friends = Vec::new();
    let affected_rows;
    match fc_settings.database.as_str() {
        "sqlite" => {
            // get sqlite conn pool
            let dbpool = sqlite::connect_sqlite_dbpool("data.db").await.unwrap();
            match sqlx::migrate!("../db/schema/sqlite").run(&dbpool).await {
                Ok(()) => (),
                Err(e) => {
                    info!("{}", e);
                    return;
                }
            };
            if let Err(e) = sqlite::truncate_friend_table(&dbpool).await {
                error!("{}", e);
                return;
            }
            for mut crawl_res in all_res {
                if !crawl_res.1.is_empty() {
                    let posts = crawl_res.1.iter().map(|post| {
                        metadata::Posts::new(
                            post.clone(),
                            crawl_res.0.name.clone(),
                            crawl_res.0.avatar.clone(),
                            tools::strptime_to_string_ymdhms(now),
                        )
                    });
                    if let Err(e) = sqlite::delete_post_table(posts.clone(), &dbpool).await {
                        error!("{}", e);
                        return;
                    }
                    if let Err(e) = sqlite::bulk_insert_post_table(posts, &dbpool).await {
                        error!("{}", e);
                        return;
                    }
                    if let Err(e) = sqlite::insert_friend_table(&crawl_res.0, &dbpool).await {
                        error!("{}", e);
                        return;
                    }
                    success_friends.push(crawl_res.0);
                    success_posts.push(crawl_res.1);
                } else {
                    crawl_res.0.error = true;
                    if let Err(e) = sqlite::insert_friend_table(&crawl_res.0, &dbpool).await {
                        error!("{}", e);
                        return;
                    }
                    failed_friends.push(crawl_res.0);
                }
            }

            // outdated posts cleanup
            affected_rows =
                match sqlite::delete_outdated_posts(fc_settings.outdate_clean, &dbpool).await {
                    Ok(v) => v,
                    Err(e) => {
                        error!("清理过期文章失败:{}", e);
                        0
                    }
                };
            if fc_settings.simple_mode
                && let Err(e) = write_data_to_json(&dbpool).await
            {
                info!("写入JSON数据失败: {}", e);
            }
        }
        "mysql" => {
            // get mysql conn pool
            let mysqlconnstr = match tools::get_env_var("MYSQL_URI") {
                Ok(mysqlconnstr) => mysqlconnstr,
                Err(e) => {
                    error!("{}", e);
                    return;
                }
            };
            let dbpool = match mysql::connect_mysql_dbpool(&mysqlconnstr).await {
                Ok(dbpool) => dbpool,
                Err(e) => {
                    error!("{}", e);
                    return;
                }
            };
            match sqlx::migrate!("../db/schema/mysql").run(&dbpool).await {
                Ok(()) => (),
                Err(e) => {
                    info!("{}", e);
                    return;
                }
            };
            if let Err(e) = mysql::truncate_friend_table(&dbpool).await {
                error!("{}", e);
                return;
            }
            for mut crawl_res in all_res {
                if !crawl_res.1.is_empty() {
                    let posts = crawl_res.1.iter().map(|post| {
                        metadata::Posts::new(
                            post.clone(),
                            crawl_res.0.name.clone(),
                            crawl_res.0.avatar.clone(),
                            tools::strptime_to_string_ymdhms(now),
                        )
                    });
                    if let Err(e) = mysql::delete_post_table(posts.clone(), &dbpool).await {
                        error!("{}", e);
                        return;
                    }
                    if let Err(e) = mysql::bulk_insert_post_table(posts, &dbpool).await {
                        error!("{}", e);
                        return;
                    }
                    if let Err(e) = mysql::insert_friend_table(&crawl_res.0, &dbpool).await {
                        error!("{}", e);
                        return;
                    }
                    success_friends.push(crawl_res.0);
                    success_posts.push(crawl_res.1);
                } else {
                    crawl_res.0.error = true;
                    if let Err(e) = mysql::insert_friend_table(&crawl_res.0, &dbpool).await {
                        error!("{}", e);
                        return;
                    }
                    failed_friends.push(crawl_res.0);
                }
            }

            // outdated posts cleanup
            affected_rows =
                match mysql::delete_outdated_posts(fc_settings.outdate_clean, &dbpool).await {
                    Ok(v) => v,
                    Err(e) => {
                        error!("清理过期文章失败:{}", e);
                        0
                    }
                };
        }
        "mongodb" => {
            let mongodburi = match tools::get_env_var("MONGODB_URI") {
                Ok(mongodburi) => mongodburi,
                Err(e) => {
                    error!("{}", e);
                    return;
                }
            };
            let clientdb = match mongo::connect_mongodb_clientdb(&mongodburi).await {
                Ok(clientdb) => clientdb,
                Err(e) => {
                    error!("{}", e);
                    return;
                }
            };
            if let Err(e) = mongo::truncate_friend_table(&clientdb).await {
                error!("{}", e);
                return;
            }
            for mut crawl_res in all_res {
                if !crawl_res.1.is_empty() {
                    let posts = crawl_res.1.iter().map(|post| {
                        metadata::Posts::new(
                            post.clone(),
                            crawl_res.0.name.clone(),
                            crawl_res.0.avatar.clone(),
                            tools::strptime_to_string_ymdhms(now),
                        )
                    });
                    if let Err(e) = mongo::delete_post_table(posts.clone(), &clientdb).await {
                        error!("{}", e);
                        return;
                    }
                    if let Err(e) = mongo::bulk_insert_post_table(posts, &clientdb).await {
                        error!("{}", e);
                        return;
                    }
                    if let Err(e) = mongo::insert_friend_table(&crawl_res.0, &clientdb).await {
                        error!("{}", e);
                        return;
                    }
                    success_friends.push(crawl_res.0);
                    success_posts.push(crawl_res.1);
                } else {
                    crawl_res.0.error = true;
                    if let Err(e) = mongo::insert_friend_table(&crawl_res.0, &clientdb).await {
                        error!("{}", e);
                        return;
                    }
                    failed_friends.push(crawl_res.0);
                }
            }

            // outdated posts cleanup
            affected_rows =
                match mongo::delete_outdated_posts(fc_settings.outdate_clean, &clientdb).await {
                    Ok(v) => v,
                    Err(e) => {
                        error!("清理过期文章失败:{}", e);
                        0
                    }
                };
        }
        _ => return,
    };

    info!(
        "成功友链数 {}，失败友链数 {}",
        success_friends.len(),
        failed_friends.len()
    );
    info!(
        "本次获取总文章数 {}",
        success_posts.iter().fold(0, |acc, x| { acc + x.len() })
    );
    info!(
        "清理过期文章(距今超过{}天) {} 条",
        fc_settings.outdate_clean, affected_rows
    );
    info!(
        "失联友链明细 {}",
        serde_json::to_string_pretty(&failed_friends).unwrap()
    );

    // 生成文章摘要
    if let Err(e) = generate_article_summaries(&fc_settings, &client).await {
        error!("生成文章摘要失败: {}", e);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use data_structures::metadata::ArticleSummary;

    #[test]
    fn test_should_update_summary_content_unchanged_summary_exists() {
        let summary = ArticleSummary {
            link: "test".to_string(),
            content_hash: "hash123".to_string(),
            summary: "existing summary".to_string(),
            ai_model: Some("test-model".to_string()),
            created_at: "2023-01-01".to_string(),
            updated_at: "2023-01-01".to_string(),
        };

        let (should_update, reason) = should_update_summary(&summary, "hash123");

        assert!(!should_update);
        assert_eq!(reason, "内容未变化且摘要存在");
    }

    #[test]
    fn test_should_update_summary_content_changed() {
        let summary = ArticleSummary {
            link: "test".to_string(),
            content_hash: "hash123".to_string(),
            summary: "existing summary".to_string(),
            ai_model: Some("test-model".to_string()),
            created_at: "2023-01-01".to_string(),
            updated_at: "2023-01-01".to_string(),
        };

        let (should_update, reason) = should_update_summary(&summary, "hash456");

        assert!(should_update);
        assert_eq!(reason, "内容已变化");
    }

    #[test]
    fn test_should_update_summary_empty_summary() {
        let summary = ArticleSummary {
            link: "test".to_string(),
            content_hash: "hash123".to_string(),
            summary: "".to_string(),
            ai_model: Some("test-model".to_string()),
            created_at: "2023-01-01".to_string(),
            updated_at: "2023-01-01".to_string(),
        };

        let (should_update, reason) = should_update_summary(&summary, "hash123");

        assert!(should_update);
        assert_eq!(reason, "摘要为空");
    }

    #[test]
    fn test_should_update_summary_whitespace_only_summary() {
        let summary = ArticleSummary {
            link: "test".to_string(),
            content_hash: "hash123".to_string(),
            summary: "   \n\t  ".to_string(),
            ai_model: Some("test-model".to_string()),
            created_at: "2023-01-01".to_string(),
            updated_at: "2023-01-01".to_string(),
        };

        let (should_update, reason) = should_update_summary(&summary, "hash123");

        assert!(should_update);
        assert_eq!(reason, "摘要为空");
    }

    #[test]
    fn test_should_update_summary_empty_and_content_changed() {
        let summary = ArticleSummary {
            link: "test".to_string(),
            content_hash: "hash123".to_string(),
            summary: "".to_string(),
            ai_model: Some("test-model".to_string()),
            created_at: "2023-01-01".to_string(),
            updated_at: "2023-01-01".to_string(),
        };

        let (should_update, reason) = should_update_summary(&summary, "hash456");

        assert!(should_update);
        // 当摘要为空时，优先显示"摘要为空"原因
        assert_eq!(reason, "摘要为空");
    }
}
