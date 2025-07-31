use chrono::{Duration, Local};
use data_structures::metadata::{self, ArticleSummary, Friends, Posts};
use futures::TryStreamExt;
use mongodb::{
    Client, Database as MongoDatabase,
    bson::{Regex, doc},
    error::Error,
    options::ClientOptions,
};

pub async fn connect_mongodb_clientdb(
    mongodburi: &str,
) -> Result<MongoDatabase, Box<dyn std::error::Error>> {
    let client_options = ClientOptions::parse(mongodburi).await?;
    let client = Client::with_options(client_options)?;
    Ok(client.database("fcircle"))
}

pub async fn insert_post_table(
    post: &Posts,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Posts>("Posts");
    collection.insert_one(post).await?;
    Ok(())
}

pub async fn insert_friend_table(
    friends: &Friends,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Friends>("Friends");
    collection.insert_one(friends).await?;
    Ok(())
}

pub async fn bulk_insert_post_table(
    tuples: impl Iterator<Item = metadata::Posts>,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Posts>("Posts");
    collection.insert_many(tuples).await?;
    Ok(())
}

pub async fn bulk_insert_friend_table(
    tuples: impl Iterator<Item = Friends>,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Friends>("Friends");
    collection.insert_many(tuples).await?;
    Ok(())
}

pub async fn delete_post_table(
    tuples: impl Iterator<Item = Posts>,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Posts>("Posts");
    for posts in tuples {
        let filter = doc! { "link": posts.meta.link,"author":posts.author };
        collection.delete_many(filter).await?;
    }
    Ok(())
}

pub async fn truncate_friend_table(db: &MongoDatabase) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Friends>("Friends");
    collection.drop().await?;
    Ok(())
}

/// 查询`posts`表
///
/// 按照`sort_rule`排序；
///
/// 如果`start`和`end`同时为0，则查询全部；
///
/// 否则只查询`start-end`条数据，如果`start>end`，会报错
pub async fn select_all_from_posts(
    pool: &MongoDatabase,
    start: usize,
    end: usize,
    sort_rule: &str,
) -> Result<Vec<metadata::Posts>, Error> {
    let collection = pool.collection::<Posts>("Posts");
    let cursor = if start == 0 && end == 0 {
        collection.find(doc! {}).sort(doc! {sort_rule: -1}).await?
    } else {
        collection
            .find(doc! {})
            .sort(doc! {sort_rule: -1})
            .limit((end - start) as i64)
            .skip(start as u64)
            .await?
    };
    let posts = cursor.try_collect().await?;
    Ok(posts)
}

/// 查询`posts`表的所有数据，并通过aggregation pipeline JOIN `ArticleSummaries`集合获取摘要信息
///
/// 当start==0并且end==0时，返回所有数据，
/// 否则只查询`start-end`条数据，如果`start>end`，会报错
pub async fn select_all_from_posts_with_summary(
    pool: &MongoDatabase,
    start: usize,
    end: usize,
    sort_rule: &str,
) -> Result<Vec<metadata::PostsWithSummary>, Box<dyn std::error::Error>> {
    let collection = pool.collection::<mongodb::bson::Document>("Posts");

    // 构建聚合管道
    let mut pipeline = vec![
        // 1. 左连接 ArticleSummaries 集合
        doc! {
            "$lookup": {
                "from": "ArticleSummaries",
                "localField": "link",
                "foreignField": "link",
                "as": "summary_info"
            }
        },
        // 2. 展开 summary_info 数组（如果存在）
        doc! {
            "$addFields": {
                "summary_data": {
                    "$arrayElemAt": ["$summary_info", 0]
                }
            }
        },
        // 3. 投影字段
        doc! {
            "$project": {
                "title": 1,
                "created": 1,
                "updated": 1,
                "link": 1,
                "author": 1,
                "avatar": 1,
                "rule": 1,
                "createdAt": 1,
                "summary": { "$ifNull": ["$summary_data.summary", null] },
                "ai_model": { "$ifNull": ["$summary_data.ai_model", null] },
                "summary_created_at": { "$ifNull": ["$summary_data.createdAt", null] },
                "summary_updated_at": { "$ifNull": ["$summary_data.updatedAt", null] }
            }
        },
        // 4. 排序
        doc! {
            "$sort": { sort_rule: -1 }
        },
    ];

    // 5. 如果需要分页，添加skip和limit
    if start != 0 || end != 0 {
        pipeline.push(doc! { "$skip": start as i64 });
        pipeline.push(doc! { "$limit": (end - start) as i64 });
    }

    let mut cursor = collection.aggregate(pipeline).await?;
    let mut posts_with_summary = Vec::new();

    while let Some(doc) = cursor.try_next().await? {
        // 手动构建 PostsWithSummary
        let base_post = metadata::BasePosts::new(
            doc.get_str("title").unwrap_or("").to_string(),
            doc.get_str("created").unwrap_or("").to_string(),
            doc.get_str("updated").unwrap_or("").to_string(),
            doc.get_str("link").unwrap_or("").to_string(),
            doc.get_str("rule").unwrap_or("").to_string(),
        );

        let post_with_summary = metadata::PostsWithSummary::new(
            base_post,
            doc.get_str("author").unwrap_or("").to_string(),
            doc.get_str("avatar").unwrap_or("").to_string(),
            doc.get_str("createdAt").unwrap_or("").to_string(),
            doc.get_str("summary").ok().map(|s| s.to_string()),
            doc.get_str("ai_model").ok().map(|s| s.to_string()),
            doc.get_str("summary_created_at")
                .ok()
                .map(|s| s.to_string()),
            doc.get_str("summary_updated_at")
                .ok()
                .map(|s| s.to_string()),
        );

        posts_with_summary.push(post_with_summary);
    }

    Ok(posts_with_summary)
}

/// 获取`posts`表中最近一次更新（`createdAt`最新）的时间
pub async fn select_latest_time_from_posts(pool: &MongoDatabase) -> Result<String, Error> {
    let collection = pool.collection::<Posts>("Posts");
    let cursor = collection
        .find_one(doc! {})
        .sort(doc! {"createdAt": -1})
        .await?;
    if let Some(post) = cursor {
        Ok(post.created_at)
    } else {
        Ok("1970-01-01 00:00:00".to_string())
    }
}

pub async fn select_all_from_friends(
    pool: &MongoDatabase,
) -> Result<Vec<metadata::Friends>, Error> {
    let collection = pool.collection::<Friends>("Friends");
    let cursor = collection.find(doc! {}).await?;
    let friends = cursor.try_collect().await?;
    Ok(friends)
}

/// 查询`friends`表中`link`包含`domain_str`的一条数据
pub async fn select_one_from_friends_with_linklike(
    pool: &MongoDatabase,
    domain_str: &str,
) -> Result<metadata::Friends, Error> {
    let collection = pool.collection::<Friends>("Friends");
    // let cursor = collection.find_one(doc! {"link": {'$regex': domain_str}}).await?;
    let re = Regex {
        pattern: domain_str.to_string(),
        options: String::new(),
    };
    let friend = collection
        .find_one(doc! {"link": re})
        .await?
        .ok_or(Error::custom("not found"))?;
    Ok(friend)
}

/// 查询`posts`表中`link`包含`domain_str`的数据
///
/// 当num<0时，返回所有数据
pub async fn select_all_from_posts_with_linklike(
    pool: &MongoDatabase,
    link: &str,
    num: i32,
    sort_rule: &str,
) -> Result<Vec<metadata::Posts>, Error> {
    let collection = pool.collection::<Posts>("Posts");
    let re = Regex {
        pattern: link.to_string(),
        options: String::new(),
    };
    let cursor = if num > 0 {
        collection
            .find(doc! {"link": re})
            .sort(doc! {sort_rule: -1})
            .limit(num as i64)
            .await?
    } else {
        collection
            .find(doc! {"link": re})
            .sort(doc! {sort_rule: -1})
            .await?
    };

    let posts = cursor.try_collect().await?;
    Ok(posts)
}

pub async fn delete_outdated_posts(days: usize, clientdb: &MongoDatabase) -> Result<usize, Error> {
    if days == 0 {
        return Ok(0);
    }
    let now = Local::now() - Duration::days(days as i64);
    let collection = clientdb.collection::<Posts>("Posts");
    let filter = doc! { "updated": doc! { "$lt": now.format("%Y-%m-%d").to_string() } };
    let result = collection.delete_many(filter).await?;
    Ok(result.deleted_count as usize)
}

// Article Summary Operations

pub async fn insert_article_summary(
    summary: &ArticleSummary,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<ArticleSummary>("ArticleSummaries");
    let filter = doc! { "link": &summary.link };
    let update = doc! {
        "$set": {
            "link": &summary.link,
            "content_hash": &summary.content_hash,
            "summary": &summary.summary,
            "ai_model": &summary.ai_model,
            "createdAt": &summary.created_at,
            "updatedAt": &summary.updated_at,
        }
    };
    let options = mongodb::options::UpdateOptions::builder()
        .upsert(true)
        .build();
    collection
        .update_one(filter, update)
        .with_options(options)
        .await?;
    Ok(())
}

pub async fn select_article_summary_by_link(
    link: &str,
    db: &MongoDatabase,
) -> Result<Option<ArticleSummary>, Box<dyn std::error::Error>> {
    let collection = db.collection::<ArticleSummary>("ArticleSummaries");
    let filter = doc! { "link": link };
    let summary = collection.find_one(filter).await?;
    Ok(summary)
}

pub async fn select_article_summary_by_hash(
    content_hash: &str,
    db: &MongoDatabase,
) -> Result<Option<ArticleSummary>, Box<dyn std::error::Error>> {
    let collection = db.collection::<ArticleSummary>("ArticleSummaries");
    let filter = doc! { "content_hash": content_hash };
    let summary = collection.find_one(filter).await?;
    Ok(summary)
}

pub async fn delete_article_summary_by_link(
    link: &str,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<ArticleSummary>("ArticleSummaries");
    let filter = doc! { "link": link };
    collection.delete_one(filter).await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use data_structures::metadata::{BasePosts, Friends, Posts};
    use std::time::SystemTime;

    // MongoDB连接URI
    const MONGODB_URI: &str = "mongodb://root:123456@127.0.0.1:27017";

    // 辅助函数：创建测试数据库连接
    async fn setup_test_db() -> MongoDatabase {
        let db = connect_mongodb_clientdb(MONGODB_URI).await.unwrap();

        // 清空集合以确保测试环境干净
        let _ = db.collection::<Friends>("Friends").drop().await;
        let _ = db.collection::<Posts>("Posts").drop().await;
        let _ = db
            .collection::<ArticleSummary>("ArticleSummaries")
            .drop()
            .await;

        db
    }

    // 测试连接数据库
    #[tokio::test]
    async fn test_connect_mongodb_clientdb() {
        let db = connect_mongodb_clientdb(MONGODB_URI).await.unwrap();
        assert_eq!(db.name(), "fcircle");
    }

    // 测试插入和查询好友
    #[tokio::test]
    async fn test_insert_and_select_friend() {
        let db = setup_test_db().await;

        // 创建测试数据
        let friend = Friends {
            name: "测试用户".to_string(),
            link: "https://example.com".to_string(),
            error: false,
            avatar: "https://example.com/avatar.jpg".to_string(),
            created_at: SystemTime::now().elapsed().unwrap().as_secs().to_string(),
        };

        // 插入数据
        insert_friend_table(&friend, &db).await.unwrap();

        // 查询数据
        let collection = db.collection::<Friends>("Friends");
        let friends: Vec<Friends> = collection
            .find(doc! {})
            .await
            .unwrap()
            .try_collect()
            .await
            .unwrap();

        // 验证结果
        assert_eq!(friends.len(), 1);
        assert_eq!(friends[0].name, "测试用户");
        assert_eq!(friends[0].link, "https://example.com");
        assert!(!friends[0].error);
    }

    // 测试插入和查询帖子
    #[tokio::test]
    async fn test_insert_and_select_post() {
        let db = setup_test_db().await;

        // 创建测试数据
        let meta = BasePosts {
            title: "测试帖子".to_string(),
            created: "2023-01-01".to_string(),
            updated: "2023-01-01".to_string(),
            link: "https://example.com/post".to_string(),
            rule: "test".to_string(),
        };

        let post = Posts {
            meta,
            author: "测试作者".to_string(),
            avatar: "https://example.com/avatar.jpg".to_string(),
            created_at: SystemTime::now().elapsed().unwrap().as_secs().to_string(),
        };

        // 插入数据
        insert_post_table(&post, &db).await.unwrap();

        // 查询数据
        let posts = select_all_from_posts(&db, 0, 0, "created_at")
            .await
            .unwrap();

        // 验证结果
        assert_eq!(posts.len(), 1);
        assert_eq!(posts[0].meta.title, "测试帖子");
        assert_eq!(posts[0].meta.link, "https://example.com/post");
        assert_eq!(posts[0].author, "测试作者");
    }

    // 测试批量插入好友
    #[tokio::test]
    async fn test_bulk_insert_friends() {
        let db = setup_test_db().await;

        // 创建测试数据
        let friends = vec![
            Friends {
                name: "用户1".to_string(),
                link: "https://example1.com".to_string(),
                error: false,
                avatar: "https://example1.com/avatar.jpg".to_string(),
                created_at: SystemTime::now().elapsed().unwrap().as_secs().to_string(),
            },
            Friends {
                name: "用户2".to_string(),
                link: "https://example2.com".to_string(),
                error: false,
                avatar: "https://example2.com/avatar.jpg".to_string(),
                created_at: SystemTime::now().elapsed().unwrap().as_secs().to_string(),
            },
        ];

        // 批量插入
        bulk_insert_friend_table(friends.into_iter(), &db)
            .await
            .unwrap();

        // 查询数据
        let collection = db.collection::<Friends>("Friends");
        let result: Vec<Friends> = collection
            .find(doc! {})
            .await
            .unwrap()
            .try_collect()
            .await
            .unwrap();

        // 验证结果
        assert_eq!(result.len(), 2);
        assert!(result.iter().any(|f| f.name == "用户1"));
        assert!(result.iter().any(|f| f.name == "用户2"));
    }

    // 测试批量插入帖子
    #[tokio::test]
    async fn test_bulk_insert_posts() {
        let db = setup_test_db().await;

        // 创建测试数据
        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "帖子1".to_string(),
                    created: "2023-01-01".to_string(),
                    updated: "2023-01-01".to_string(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者1".to_string(),
                avatar: "https://example.com/avatar1.jpg".to_string(),
                created_at: "2023-01-01".to_string(),
            },
            Posts {
                meta: BasePosts {
                    title: "帖子2".to_string(),
                    created: "2023-01-02".to_string(),
                    updated: "2023-01-02".to_string(),
                    link: "https://example.com/post2".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者2".to_string(),
                avatar: "https://example.com/avatar2.jpg".to_string(),
                created_at: "2023-01-02".to_string(),
            },
        ];

        // 批量插入
        bulk_insert_post_table(posts.into_iter(), &db)
            .await
            .unwrap();

        // 查询数据
        let result = select_all_from_posts(&db, 0, 0, "created_at")
            .await
            .unwrap();

        // 验证结果
        assert_eq!(result.len(), 2);
        assert!(result.iter().any(|p| p.meta.title == "帖子1"));
        assert!(result.iter().any(|p| p.meta.title == "帖子2"));
    }

    // 测试删除帖子
    #[tokio::test]
    async fn test_delete_posts() {
        let db = setup_test_db().await;

        // 创建测试数据
        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "帖子1".to_string(),
                    created: "2023-01-01".to_string(),
                    updated: "2023-01-01".to_string(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者1".to_string(),
                avatar: "https://example.com/avatar1.jpg".to_string(),
                created_at: "2023-01-01".to_string(),
            },
            Posts {
                meta: BasePosts {
                    title: "帖子2".to_string(),
                    created: "2023-01-02".to_string(),
                    updated: "2023-01-02".to_string(),
                    link: "https://example.com/post2".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者2".to_string(),
                avatar: "https://example.com/avatar2.jpg".to_string(),
                created_at: "2023-01-02".to_string(),
            },
        ];

        // 批量插入
        bulk_insert_post_table(posts.clone().into_iter(), &db)
            .await
            .unwrap();

        // 删除第一篇帖子
        let to_delete = vec![posts[0].clone()];
        delete_post_table(to_delete.into_iter(), &db).await.unwrap();

        // 查询数据
        let collection = db.collection::<Posts>("Posts");
        let result: Vec<Posts> = collection
            .find(doc! {})
            .await
            .unwrap()
            .try_collect()
            .await
            .unwrap();

        // 验证结果
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].meta.title, "帖子2");
    }

    // 测试清空好友表
    #[tokio::test]
    async fn test_truncate_friend_table() {
        let db = setup_test_db().await;

        // 插入测试数据
        let friend = Friends {
            name: "测试用户".to_string(),
            link: "https://example.com".to_string(),
            error: false,
            avatar: "https://example.com/avatar.jpg".to_string(),
            created_at: "2023-01-01".to_string(),
        };

        insert_friend_table(&friend, &db).await.unwrap();

        // 验证数据已插入
        let collection = db.collection::<Friends>("Friends");
        let friends: Vec<Friends> = collection
            .find(doc! {})
            .await
            .unwrap()
            .try_collect()
            .await
            .unwrap();
        assert_eq!(friends.len(), 1);

        // 清空好友表
        truncate_friend_table(&db).await.unwrap();

        // 验证表已清空
        let collection = db.collection::<Friends>("Friends");
        let count = collection.count_documents(doc! {}).await.unwrap();
        assert_eq!(count, 0);
    }

    // 测试分页查询帖子
    #[tokio::test]
    async fn test_select_posts_with_pagination() {
        let db = setup_test_db().await;

        // 创建测试数据 - 插入5篇文章
        let mut posts = Vec::new();
        for i in 1..=5 {
            posts.push(Posts {
                meta: BasePosts {
                    title: format!("帖子{i}"),
                    created: format!("2023-01-0{i}"),
                    updated: format!("2023-01-0{i}"),
                    link: format!("https://example.com/post{i}"),
                    rule: "test".to_string(),
                },
                author: format!("作者{i}"),
                avatar: format!("https://example.com/avatar{i}.jpg"),
                created_at: format!("2023-01-0{i}"),
            });
        }

        // 批量插入
        bulk_insert_post_table(posts.into_iter(), &db)
            .await
            .unwrap();

        // 测试分页查询 - 第一页，每页2条
        let page1 = select_all_from_posts(&db, 0, 2, "created_at")
            .await
            .unwrap();
        assert_eq!(page1.len(), 2);

        // 测试分页查询 - 第二页，每页2条
        let page2 = select_all_from_posts(&db, 2, 4, "created_at")
            .await
            .unwrap();
        assert_eq!(page2.len(), 2);

        // 测试分页查询 - 第三页，每页2条（最后一页可能不足2条）
        let page3 = select_all_from_posts(&db, 4, 6, "created_at")
            .await
            .unwrap();
        assert_eq!(page3.len(), 1);
    }

    // 测试获取最新更新时间
    #[tokio::test]
    async fn test_select_latest_time_from_posts() {
        let db = setup_test_db().await;
        // 插入多条不同createdAt的Posts
        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "旧帖子".to_string(),
                    created: "2023-01-01".to_string(),
                    updated: "2023-01-01".to_string(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者1".to_string(),
                avatar: "https://example.com/avatar1.jpg".to_string(),
                created_at: "2023-01-01".to_string(),
            },
            Posts {
                meta: BasePosts {
                    title: "新帖子".to_string(),
                    created: "2023-01-02".to_string(),
                    updated: "2023-01-02".to_string(),
                    link: "https://example.com/post2".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者2".to_string(),
                avatar: "https://example.com/avatar2.jpg".to_string(),
                created_at: "2023-01-02".to_string(),
            },
        ];
        bulk_insert_post_table(posts.into_iter(), &db)
            .await
            .unwrap();
        let latest_time = select_latest_time_from_posts(&db).await.unwrap();
        assert!(latest_time == "2023-01-02" || latest_time == "2023-01-01");
    }

    // 测试查询所有好友
    #[tokio::test]
    async fn test_select_all_from_friends() {
        let db = setup_test_db().await;
        let friends = vec![
            Friends {
                name: "用户1".to_string(),
                link: "https://example1.com".to_string(),
                error: false,
                avatar: "https://example1.com/avatar.jpg".to_string(),
                created_at: "2023-01-01".to_string(),
            },
            Friends {
                name: "用户2".to_string(),
                link: "https://example2.com".to_string(),
                error: false,
                avatar: "https://example2.com/avatar.jpg".to_string(),
                created_at: "2023-01-02".to_string(),
            },
        ];
        bulk_insert_friend_table(friends.into_iter(), &db)
            .await
            .unwrap();
        let result = select_all_from_friends(&db).await.unwrap();
        assert_eq!(result.len(), 2);
        assert!(result.iter().any(|f| f.name == "用户1"));
        assert!(result.iter().any(|f| f.name == "用户2"));
    }

    // 测试模糊查询好友
    #[tokio::test]
    async fn test_select_one_from_friends_with_linklike() {
        let db = setup_test_db().await;
        let friends = vec![
            Friends {
                name: "用户1".to_string(),
                link: "https://example.com".to_string(),
                error: false,
                avatar: "https://example.com/avatar.jpg".to_string(),
                created_at: "2023-01-01".to_string(),
            },
            Friends {
                name: "用户2".to_string(),
                link: "https://example.org".to_string(),
                error: false,
                avatar: "https://example.org/avatar.jpg".to_string(),
                created_at: "2023-01-02".to_string(),
            },
        ];
        bulk_insert_friend_table(friends.into_iter(), &db)
            .await
            .unwrap();
        let result = select_one_from_friends_with_linklike(&db, "example.com")
            .await
            .unwrap();
        assert_eq!(result.name, "用户1");
    }

    // 测试模糊查询帖子
    #[tokio::test]
    async fn test_select_all_from_posts_with_linklike() {
        let db = setup_test_db().await;
        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "帖子1".to_string(),
                    created: "2023-01-01".to_string(),
                    updated: "2023-01-01".to_string(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者1".to_string(),
                avatar: "https://example.com/avatar1.jpg".to_string(),
                created_at: "2023-01-01".to_string(),
            },
            Posts {
                meta: BasePosts {
                    title: "帖子2".to_string(),
                    created: "2023-01-02".to_string(),
                    updated: "2023-01-02".to_string(),
                    link: "https://example.org/post2".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者2".to_string(),
                avatar: "https://example.org/avatar2.jpg".to_string(),
                created_at: "2023-01-02".to_string(),
            },
        ];
        bulk_insert_post_table(posts.into_iter(), &db)
            .await
            .unwrap();
        // 查询特定链接的帖子
        let result = select_all_from_posts_with_linklike(&db, "example.com", -1, "created_at")
            .await
            .unwrap();
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].meta.title, "帖子1");
        // 查询限制数量
        let result = select_all_from_posts_with_linklike(&db, "example", 1, "created_at")
            .await
            .unwrap();
        assert_eq!(result.len(), 1);
    }

    // 测试删除过期帖子
    #[tokio::test]
    async fn test_delete_outdated_posts() {
        let db = setup_test_db().await;

        // 获取当前时间
        let now = Local::now();
        let today = now.format("%Y-%m-%d").to_string();
        let yesterday = (now - Duration::days(1)).format("%Y-%m-%d").to_string();
        let old_date = (now - Duration::days(35)).format("%Y-%m-%d").to_string();

        // 创建测试数据 - 包含不同更新时间的帖子
        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "新帖子".to_string(),
                    created: today.clone(),
                    updated: today.clone(), // 今天的帖子
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者1".to_string(),
                avatar: "https://example.com/avatar1.jpg".to_string(),
                created_at: today.clone(),
            },
            Posts {
                meta: BasePosts {
                    title: "旧帖子1".to_string(),
                    created: yesterday.clone(),
                    updated: yesterday.clone(), // 昨天的帖子
                    link: "https://example.com/post2".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者2".to_string(),
                avatar: "https://example.com/avatar2.jpg".to_string(),
                created_at: yesterday.clone(),
            },
            Posts {
                meta: BasePosts {
                    title: "旧帖子2".to_string(),
                    created: old_date.clone(),
                    updated: old_date.clone(), // 35天前的帖子
                    link: "https://example.com/post3".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者3".to_string(),
                avatar: "https://example.com/avatar3.jpg".to_string(),
                created_at: old_date.clone(),
            },
        ];

        // 批量插入测试数据
        bulk_insert_post_table(posts.into_iter(), &db)
            .await
            .unwrap();

        // 验证初始数据数量
        let initial_count = db
            .collection::<Posts>("Posts")
            .count_documents(doc! {})
            .await
            .unwrap();
        assert_eq!(initial_count, 3);

        // 删除30天前的过期帖子
        let deleted_count = delete_outdated_posts(30, &db).await.unwrap();

        // 验证删除结果 - 应该删除1个旧帖子（35天前的）
        assert_eq!(deleted_count, 1);

        // 验证剩余数据
        let remaining_posts = select_all_from_posts(&db, 0, 0, "created_at")
            .await
            .unwrap();

        // 应该剩下2个帖子（今天和昨天的）
        assert_eq!(remaining_posts.len(), 2);
        assert!(remaining_posts.iter().any(|p| p.meta.title == "新帖子"));
        assert!(remaining_posts.iter().any(|p| p.meta.title == "旧帖子1"));
    }

    // 测试删除过期帖子 - 边界情况：没有过期帖子
    #[tokio::test]
    async fn test_delete_outdated_posts_no_outdated() {
        let db = setup_test_db().await;

        // 获取当前时间
        let now = Local::now();
        let today = now.format("%Y-%m-%d").to_string();
        let yesterday = (now - Duration::days(1)).format("%Y-%m-%d").to_string();

        // 创建测试数据 - 只包含最近的帖子
        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "新帖子1".to_string(),
                    created: today.clone(),
                    updated: today.clone(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者1".to_string(),
                avatar: "https://example.com/avatar1.jpg".to_string(),
                created_at: today.clone(),
            },
            Posts {
                meta: BasePosts {
                    title: "新帖子2".to_string(),
                    created: yesterday.clone(),
                    updated: yesterday.clone(),
                    link: "https://example.com/post2".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者2".to_string(),
                avatar: "https://example.com/avatar2.jpg".to_string(),
                created_at: yesterday.clone(),
            },
        ];

        // 批量插入测试数据
        bulk_insert_post_table(posts.into_iter(), &db)
            .await
            .unwrap();

        // 验证初始数据数量
        let initial_count = db
            .collection::<Posts>("Posts")
            .count_documents(doc! {})
            .await
            .unwrap();
        assert_eq!(initial_count, 2);

        // 删除30天前的过期帖子（应该没有过期帖子）
        let deleted_count = delete_outdated_posts(30, &db).await.unwrap();

        // 验证删除结果 - 应该删除0个帖子
        assert_eq!(deleted_count, 0);

        // 验证数据没有变化
        let remaining_posts = select_all_from_posts(&db, 0, 0, "created_at")
            .await
            .unwrap();

        // 应该还有2个帖子
        assert_eq!(remaining_posts.len(), 2);
    }

    // 测试删除过期帖子 - 边界情况：删除所有帖子
    #[tokio::test]
    async fn test_delete_outdated_posts_all_outdated() {
        let db = setup_test_db().await;

        // 获取当前时间
        let now = Local::now();
        let old_date1 = (now - Duration::days(35)).format("%Y-%m-%d").to_string();
        let old_date2 = (now - Duration::days(40)).format("%Y-%m-%d").to_string();

        // 创建测试数据 - 只包含很旧的帖子
        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "旧帖子1".to_string(),
                    created: old_date1.clone(),
                    updated: old_date1.clone(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者1".to_string(),
                avatar: "https://example.com/avatar1.jpg".to_string(),
                created_at: old_date1.clone(),
            },
            Posts {
                meta: BasePosts {
                    title: "旧帖子2".to_string(),
                    created: old_date2.clone(),
                    updated: old_date2.clone(),
                    link: "https://example.com/post2".to_string(),
                    rule: "test".to_string(),
                },
                author: "作者2".to_string(),
                avatar: "https://example.com/avatar2.jpg".to_string(),
                created_at: old_date2.clone(),
            },
        ];

        // 批量插入测试数据
        bulk_insert_post_table(posts.into_iter(), &db)
            .await
            .unwrap();

        // 验证初始数据数量
        let initial_count = db
            .collection::<Posts>("Posts")
            .count_documents(doc! {})
            .await
            .unwrap();
        assert_eq!(initial_count, 2);

        // 删除30天前的过期帖子（应该删除所有帖子）
        let deleted_count = delete_outdated_posts(30, &db).await.unwrap();

        // 验证删除结果 - 应该删除2个帖子
        assert_eq!(deleted_count, 2);

        // 验证所有数据都被删除
        let remaining_posts = select_all_from_posts(&db, 0, 0, "created_at")
            .await
            .unwrap();

        // 应该没有剩余帖子
        assert_eq!(remaining_posts.len(), 0);
    }

    // 测试插入和查询文章摘要
    #[tokio::test]
    async fn test_insert_and_select_article_summary() {
        let db = setup_test_db().await;

        // 创建测试数据
        let summary = ArticleSummary {
            link: "https://example.com/test-article".to_string(),
            content_hash: "abc123".to_string(),
            summary: "这是一个测试摘要".to_string(),
            ai_model: Some("test-model".to_string()),
            created_at: "2023-01-01T00:00:00Z".to_string(),
            updated_at: "2023-01-01T00:00:00Z".to_string(),
        };

        // 插入数据
        insert_article_summary(&summary, &db).await.unwrap();

        // 查询数据
        let result = select_article_summary_by_link("https://example.com/test-article", &db)
            .await
            .unwrap();

        // 验证结果
        assert!(result.is_some());
        let found_summary = result.unwrap();
        assert_eq!(found_summary.link, "https://example.com/test-article");
        assert_eq!(found_summary.content_hash, "abc123");
        assert_eq!(found_summary.summary, "这是一个测试摘要");
    }

    // 测试更新文章摘要
    #[tokio::test]
    async fn test_update_article_summary() {
        let db = setup_test_db().await;

        // 插入原始数据
        let original_summary = ArticleSummary {
            link: "https://example.com/article".to_string(),
            content_hash: "hash1".to_string(),
            summary: "原始摘要".to_string(),
            ai_model: Some("original-model".to_string()),
            created_at: "2023-01-01T00:00:00Z".to_string(),
            updated_at: "2023-01-01T00:00:00Z".to_string(),
        };

        insert_article_summary(&original_summary, &db)
            .await
            .unwrap();

        // 更新数据（通过重新插入相同link的记录）
        let updated_summary = ArticleSummary {
            link: "https://example.com/article".to_string(),
            content_hash: "hash2".to_string(),
            summary: "更新后的摘要".to_string(),
            ai_model: Some("updated-model".to_string()),
            created_at: "2023-01-01T00:00:00Z".to_string(),
            updated_at: "2023-01-02T00:00:00Z".to_string(),
        };

        insert_article_summary(&updated_summary, &db).await.unwrap();

        // 查询更新后的数据
        let result = select_article_summary_by_link("https://example.com/article", &db)
            .await
            .unwrap();

        // 验证更新结果
        assert!(result.is_some());
        let found_summary = result.unwrap();
        assert_eq!(found_summary.content_hash, "hash2");
        assert_eq!(found_summary.summary, "更新后的摘要");
        assert_eq!(found_summary.updated_at, "2023-01-02T00:00:00Z");
    }

    // 测试删除文章摘要
    #[tokio::test]
    async fn test_delete_article_summary() {
        let db = setup_test_db().await;

        // 插入测试数据
        let summary = ArticleSummary {
            link: "https://example.com/to-delete".to_string(),
            content_hash: "delete_hash".to_string(),
            summary: "要删除的摘要".to_string(),
            ai_model: Some("delete-model".to_string()),
            created_at: "2023-01-01T00:00:00Z".to_string(),
            updated_at: "2023-01-01T00:00:00Z".to_string(),
        };

        insert_article_summary(&summary, &db).await.unwrap();

        // 验证数据存在
        let result = select_article_summary_by_link("https://example.com/to-delete", &db)
            .await
            .unwrap();
        assert!(result.is_some());

        // 删除数据
        delete_article_summary_by_link("https://example.com/to-delete", &db)
            .await
            .unwrap();

        // 验证数据已删除
        let result = select_article_summary_by_link("https://example.com/to-delete", &db)
            .await
            .unwrap();
        assert!(result.is_none());
    }

    // 测试查询不存在的文章摘要
    #[tokio::test]
    async fn test_select_nonexistent_article_summary() {
        let db = setup_test_db().await;

        // 查询不存在的链接
        let result = select_article_summary_by_link("https://nonexistent.com", &db)
            .await
            .unwrap();

        // 验证结果为空
        assert!(result.is_none());
    }

    // 测试根据内容哈希查询文章摘要
    #[tokio::test]
    async fn test_select_article_summary_by_hash() {
        let db = setup_test_db().await;

        // 插入测试数据
        let summary = ArticleSummary {
            link: "https://example.com/hash-test".to_string(),
            content_hash: "unique_hash_123".to_string(),
            summary: "根据哈希查询的摘要".to_string(),
            ai_model: Some("hash-test-model".to_string()),
            created_at: "2023-01-01T00:00:00Z".to_string(),
            updated_at: "2023-01-01T00:00:00Z".to_string(),
        };

        insert_article_summary(&summary, &db).await.unwrap();

        // 根据内容哈希查询
        let result = select_article_summary_by_hash("unique_hash_123", &db)
            .await
            .unwrap();

        // 验证结果
        assert!(result.is_some());
        let found_summary = result.unwrap();
        assert_eq!(found_summary.link, "https://example.com/hash-test");
        assert_eq!(found_summary.content_hash, "unique_hash_123");
        assert_eq!(found_summary.summary, "根据哈希查询的摘要");
    }
}
