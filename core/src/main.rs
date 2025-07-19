use std::fs::File;

use chrono::Utc;
use data_structures::metadata::{self};
use data_structures::response::AllPostData;
use db::{SqlitePool, mongo, mysql, sqlite};
use downloader::download;
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

#[tokio::main]
async fn main() {
    let _guard = tools::init_tracing(
        "core",
        Some("error,core=debug,db=debug,downloader=debug,tools=debug,data_structures=debug"),
    );

    let now = Utc::now().with_timezone(&downloader::BEIJING_OFFSET.unwrap());

    let css_rules: tools::Value = tools::get_yaml("./css_rules.yaml").unwrap();
    let fc_settings = tools::get_yaml_settings("./fc_settings.yaml").unwrap();

    let client = download::build_client();

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
        // TODO json_api impl
        let settings_friend_postpages = fc_settings.settings_friends_links.list.clone();
        for postpage_vec in settings_friend_postpages {
            let tm = now;
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
}
