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
    let collection = db.collection::<Posts>("Post");
    collection.insert_one(post).await?;
    Ok(())
}

pub async fn insert_friend_table(
    friends: &Friends,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Friends>("Friend");
    collection.insert_one(friends).await?;
    Ok(())
}

pub async fn bulk_insert_post_table(
    tuples: impl Iterator<Item = metadata::Posts>,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Posts>("Post");
    collection.insert_many(tuples).await?;
    Ok(())
}

pub async fn bulk_insert_friend_table(
    tuples: impl Iterator<Item = Friends>,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Friends>("Friend");
    collection.insert_many(tuples).await?;
    Ok(())
}

pub async fn delete_post_table(
    tuples: impl Iterator<Item = Posts>,
    db: &MongoDatabase,
) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Posts>("Post");
    for posts in tuples {
        let filter = doc! { "link": posts.meta.link,"author":posts.author };
        collection.delete_many(filter).await?;
    }
    Ok(())
}

pub async fn truncate_friend_table(db: &MongoDatabase) -> Result<(), Box<dyn std::error::Error>> {
    let collection = db.collection::<Friends>("Friend");
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
    let collection = pool.collection::<Posts>("Post");
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
    let collection = pool.collection::<mongodb::bson::Document>("Post");

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
                "description": 1,
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
    if start > 0 {
        pipeline.push(doc! { "$skip": start as i64 });
    }
    if end > 0 && end > start {
        pipeline.push(doc! { "$limit": (end - start) as i64 });
    }

    let mut cursor = collection.aggregate(pipeline).await?;
    let mut posts_with_summary = Vec::new();

    while let Some(doc) = cursor.try_next().await? {
        // 手动构建 PostsWithSummary
        let base_post = metadata::BasePosts::new_with_description(
            doc.get_str("title").unwrap_or("").to_string(),
            doc.get_str("created").unwrap_or("").to_string(),
            doc.get_str("updated").unwrap_or("").to_string(),
            doc.get_str("link").unwrap_or("").to_string(),
            doc.get_str("rule").unwrap_or("").to_string(),
            doc.get_str("description").ok().map(|s| s.to_string()),
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
    let collection = pool.collection::<Posts>("Post");
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
    let collection = pool.collection::<Friends>("Friend");
    let cursor = collection.find(doc! {}).await?;
    let friends = cursor.try_collect().await?;
    Ok(friends)
}

/// 查询`friends`表中`link`包含`domain_str`的一条数据
pub async fn select_one_from_friends_with_linklike(
    pool: &MongoDatabase,
    domain_str: &str,
) -> Result<metadata::Friends, Error> {
    let collection = pool.collection::<Friends>("Friend");
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
    let collection = pool.collection::<Posts>("Post");
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

/// 根据 author 名字查询文章
pub async fn select_posts_by_author(
    pool: &MongoDatabase,
    author: &str,
    num: i32,
    sort_rule: &str,
) -> Result<Vec<metadata::Posts>, Error> {
    let collection = pool.collection::<Posts>("Post");
    let cursor = if num > 0 {
        collection
            .find(doc! {"author": author})
            .sort(doc! {sort_rule: -1})
            .limit(num as i64)
            .await?
    } else {
        collection
            .find(doc! {"author": author})
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
    let collection = clientdb.collection::<Posts>("Post");
    let filter = doc! {
        "updated": doc! {
            "$lt": now.format("%Y-%m-%d").to_string(),
            "$ne": ""
        }
    };
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
        let _ = db.collection::<Friends>("Friend").drop().await;
        let _ = db.collection::<Posts>("Post").drop().await;
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

        let friend = Friends {
            name: "测试用户".to_string(),
            link: "https://example.com".to_string(),
            error: false,
            avatar: "https://example.com/avatar.jpg".to_string(),
            created_at: SystemTime::now().elapsed().unwrap().as_secs().to_string(),
        };

        insert_friend_table(&friend, &db).await.unwrap();

        let collection = db.collection::<Friends>("Friend");
        let friends: Vec<Friends> = collection
            .find(doc! {})
            .await
            .unwrap()
            .try_collect()
            .await
            .unwrap();

        assert_eq!(friends.len(), 1);
        assert_eq!(friends[0].name, "测试用户");
        assert_eq!(friends[0].link, "https://example.com");
        assert!(!friends[0].error);
    }

    // 测试插入和查询帖子
    #[tokio::test]
    async fn test_insert_and_select_post() {
        let db = setup_test_db().await;

        let meta = BasePosts {
            title: "测试帖子".to_string(),
            created: "2023-01-01".to_string(),
            updated: "2023-01-01".to_string(),
            link: "https://example.com/post".to_string(),
            rule: "test".to_string(),
            description: None,
        };

        let post = Posts {
            meta,
            author: "测试作者".to_string(),
            avatar: "https://example.com/avatar.jpg".to_string(),
            created_at: SystemTime::now().elapsed().unwrap().as_secs().to_string(),
        };

        insert_post_table(&post, &db).await.unwrap();

        let posts = select_all_from_posts(&db, 0, 0, "created_at")
            .await
            .unwrap();

        assert_eq!(posts.len(), 1);
        assert_eq!(posts[0].meta.title, "测试帖子");
        assert_eq!(posts[0].meta.link, "https://example.com/post");
        assert_eq!(posts[0].author, "测试作者");
    }

    // 测试批量插入
    #[tokio::test]
    async fn test_bulk_insert_posts() {
        let db = setup_test_db().await;

        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "帖子1".to_string(),
                    created: "2023-01-01".to_string(),
                    updated: "2023-01-01".to_string(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                    description: None,
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
                    description: None,
                },
                author: "作者2".to_string(),
                avatar: "https://example.com/avatar2.jpg".to_string(),
                created_at: "2023-01-02".to_string(),
            },
        ];

        bulk_insert_post_table(posts.into_iter(), &db)
            .await
            .unwrap();

        let result = select_all_from_posts(&db, 0, 0, "created_at")
            .await
            .unwrap();

        assert_eq!(result.len(), 2);
    }

    // 测试删除帖子
    #[tokio::test]
    async fn test_delete_posts() {
        let db = setup_test_db().await;

        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "帖子1".to_string(),
                    created: "2023-01-01".to_string(),
                    updated: "2023-01-01".to_string(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                    description: None,
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
                    description: None,
                },
                author: "作者2".to_string(),
                avatar: "https://example.com/avatar2.jpg".to_string(),
                created_at: "2023-01-02".to_string(),
            },
        ];

        bulk_insert_post_table(posts.clone().into_iter(), &db)
            .await
            .unwrap();

        let to_delete = vec![posts[0].clone()];
        delete_post_table(to_delete.into_iter(), &db).await.unwrap();

        let collection = db.collection::<Posts>("Post");
        let result: Vec<Posts> = collection
            .find(doc! {})
            .await
            .unwrap()
            .try_collect()
            .await
            .unwrap();

        assert_eq!(result.len(), 1);
        assert_eq!(result[0].meta.title, "帖子2");
    }

    // 测试清空好友表
    #[tokio::test]
    async fn test_truncate_friend_table() {
        let db = setup_test_db().await;

        let friend = Friends {
            name: "测试用户".to_string(),
            link: "https://example.com".to_string(),
            error: false,
            avatar: "https://example.com/avatar.jpg".to_string(),
            created_at: "2023-01-01".to_string(),
        };

        insert_friend_table(&friend, &db).await.unwrap();

        let collection = db.collection::<Friends>("Friend");
        let count = collection.count_documents(doc! {}).await.unwrap();
        assert_eq!(count, 1);

        truncate_friend_table(&db).await.unwrap();

        let collection = db.collection::<Friends>("Friend");
        let count = collection.count_documents(doc! {}).await.unwrap();
        assert_eq!(count, 0);
    }

    // 测试获取最新更新时间
    #[tokio::test]
    async fn test_select_latest_time_from_posts() {
        let db = setup_test_db().await;
        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "旧帖子".to_string(),
                    created: "2023-01-01".to_string(),
                    updated: "2023-01-01".to_string(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                    description: None,
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
                    description: None,
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

    // 测试删除过期帖子
    #[tokio::test]
    async fn test_delete_outdated_posts() {
        let db = setup_test_db().await;

        let now = Local::now();
        let today = now.format("%Y-%m-%d").to_string();
        let old_date = (now - Duration::days(35)).format("%Y-%m-%d").to_string();

        let posts = vec![
            Posts {
                meta: BasePosts {
                    title: "新帖子".to_string(),
                    created: today.clone(),
                    updated: today.clone(),
                    link: "https://example.com/post1".to_string(),
                    rule: "test".to_string(),
                    description: None,
                },
                author: "作者1".to_string(),
                avatar: "https://example.com/avatar1.jpg".to_string(),
                created_at: today.clone(),
            },
            Posts {
                meta: BasePosts {
                    title: "旧帖子".to_string(),
                    created: old_date.clone(),
                    updated: old_date.clone(),
                    link: "https://example.com/post2".to_string(),
                    rule: "test".to_string(),
                    description: None,
                },
                author: "作者2".to_string(),
                avatar: "https://example.com/avatar2.jpg".to_string(),
                created_at: old_date.clone(),
            },
        ];

        bulk_insert_post_table(posts.into_iter(), &db)
            .await
            .unwrap();

        let deleted_count = delete_outdated_posts(30, &db).await.unwrap();
        assert_eq!(deleted_count, 1);

        let remaining = select_all_from_posts(&db, 0, 0, "created_at")
            .await
            .unwrap();
        assert_eq!(remaining.len(), 1);
        assert_eq!(remaining[0].meta.title, "新帖子");
    }

    // 测试文章摘要操作
    #[tokio::test]
    async fn test_article_summary_crud() {
        let db = setup_test_db().await;

        let summary = ArticleSummary {
            link: "https://example.com/test-article".to_string(),
            content_hash: "abc123".to_string(),
            summary: "这是一个测试摘要".to_string(),
            ai_model: Some("test-model".to_string()),
            created_at: "2023-01-01T00:00:00Z".to_string(),
            updated_at: "2023-01-01T00:00:00Z".to_string(),
        };

        insert_article_summary(&summary, &db).await.unwrap();

        let result = select_article_summary_by_link("https://example.com/test-article", &db)
            .await
            .unwrap();
        assert!(result.is_some());
        let found = result.unwrap();
        assert_eq!(found.summary, "这是一个测试摘要");

        delete_article_summary_by_link("https://example.com/test-article", &db)
            .await
            .unwrap();

        let result = select_article_summary_by_link("https://example.com/test-article", &db)
            .await
            .unwrap();
        assert!(result.is_none());
    }
}
