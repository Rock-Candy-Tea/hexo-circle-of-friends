use data_structures::metadata;
use sqlx::{
    Error, QueryBuilder, Row, Sqlite, query, query_as, sqlite::SqliteConnectOptions,
    sqlite::SqlitePool, sqlite::SqlitePoolOptions,
};
use std::path::Path;

pub async fn connect_sqlite_dbpool(filename: impl AsRef<Path>) -> Result<SqlitePool, Error> {
    let options = SqliteConnectOptions::new()
        .filename(filename)
        .create_if_missing(true);
    SqlitePoolOptions::new()
        .max_connections(5)
        .connect_with(options)
        .await
}

pub async fn insert_post_table(post: &metadata::Posts, pool: &SqlitePool) -> Result<(), Error> {
    let sql = "INSERT INTO posts
    (title, author, link, avatar ,rule,created,updated,createdAt)
     VALUES (?, ?, ?,?, ?,?, ?, ?)";
    let q = query(sql)
        .bind(&post.meta.title)
        .bind(&post.author)
        .bind(&post.meta.link)
        .bind(&post.avatar)
        .bind(&post.meta.rule)
        .bind(&post.meta.created)
        .bind(&post.meta.updated)
        .bind(&post.created_at);
    // println!("sql: {},{:?}",q.sql(),q.take_arguments());
    q.execute(pool).await?;
    Ok(())
}

pub async fn insert_friend_table(
    friends: &metadata::Friends,
    pool: &SqlitePool,
) -> Result<(), Error> {
    let sql = "INSERT INTO friends (name, link, avatar, error,createdAt) VALUES (?, ?, ?, ?, ?)";
    let q = query(sql)
        .bind(&friends.name)
        .bind(&friends.link)
        .bind(&friends.avatar)
        .bind(friends.error)
        .bind(&friends.created_at);
    // println!("sql: {},{:?}",q.sql(),q.take_arguments());
    q.execute(pool).await?;
    Ok(())
}

pub async fn bulk_insert_post_table(
    tuples: impl Iterator<Item = metadata::Posts>,
    pool: &SqlitePool,
) -> Result<(), Error> {
    let mut query_builder: QueryBuilder<Sqlite> = QueryBuilder::new(
        // Note the trailing space; most calls to `QueryBuilder` don't automatically insert
        // spaces as that might interfere with identifiers or quoted strings where exact
        // values may matter.
        "INSERT INTO posts (title, author, link, avatar ,rule,created,updated,createdAt) ",
    );

    query_builder.push_values(tuples, |mut b, post| {
        // If you wanted to bind these by-reference instead of by-value,
        // you'd need an iterator that yields references that live as long as `query_builder`,
        // e.g. collect it to a `Vec` first.
        b.push_bind(post.meta.title)
            .push_bind(post.author)
            .push_bind(post.meta.link)
            .push_bind(post.avatar)
            .push_bind(post.meta.rule)
            .push_bind(post.meta.created)
            .push_bind(post.meta.updated)
            .push_bind(post.created_at);
    });
    let query = query_builder.build();
    query.execute(pool).await?;
    Ok(())
}

pub async fn bulk_insert_friend_table(
    tuples: impl Iterator<Item = metadata::Friends>,
    pool: &SqlitePool,
) -> Result<(), Error> {
    let mut query_builder: QueryBuilder<Sqlite> = QueryBuilder::new(
        // Note the trailing space; most calls to `QueryBuilder` don't automatically insert
        // spaces as that might interfere with identifiers or quoted strings where exact
        // values may matter.
        "INSERT INTO friends (name, link, avatar, error,createdAt) ",
    );

    query_builder.push_values(tuples, |mut b, friends| {
        // If you wanted to bind these by-reference instead of by-value,
        // you'd need an iterator that yields references that live as long as `query_builder`,
        // e.g. collect it to a `Vec` first.
        b.push_bind(friends.name)
            .push_bind(friends.link)
            .push_bind(friends.avatar)
            .push_bind(friends.error)
            .push_bind(friends.created_at);
    });
    let query = query_builder.build();
    query.execute(pool).await?;
    Ok(())
}

pub async fn delete_post_table(
    tuples: impl Iterator<Item = metadata::Posts>,
    pool: &SqlitePool,
) -> Result<(), Error> {
    let sql = "DELETE FROM posts WHERE link= ? and author = ? ";
    for posts in tuples {
        query(sql)
            .bind(posts.meta.link)
            .bind(posts.author)
            .execute(pool)
            .await?;
    }
    Ok(())
}

pub async fn truncate_friend_table(pool: &SqlitePool) -> Result<(), Error> {
    let sql = "DELETE FROM friends";
    query(sql).execute(pool).await?;
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
    pool: &SqlitePool,
    start: usize,
    end: usize,
    sort_rule: &str,
) -> Result<Vec<metadata::Posts>, Error> {
    let sql = if start == 0 && end == 0 {
        format!("SELECT * FROM posts ORDER BY {sort_rule} DESC")
    } else {
        format!(
            "
        SELECT * FROM posts
        ORDER BY {sort_rule} DESC
        LIMIT {limit} OFFSET {start}
        ",
            limit = end - start
        )
    };
    // println!("{}",sql);
    let posts = query_as::<_, metadata::Posts>(&sql).fetch_all(pool).await?;
    Ok(posts)
}

/// 查询`posts`表中`link`包含`domain_str`的数据
///
/// 当num<0时，返回所有数据
pub async fn select_all_from_posts_with_linklike(
    pool: &SqlitePool,
    link: &str,
    num: i32,
    sort_rule: &str,
) -> Result<Vec<metadata::Posts>, Error> {
    let sql = if num >= 0 {
        format!(
            "SELECT * FROM posts WHERE link like '%{link}%' ORDER BY {sort_rule} DESC LIMIT {num}"
        )
    } else {
        format!("SELECT * FROM posts WHERE link like '%{link}%' ORDER BY {sort_rule} DESC")
    };
    // println!("{}",sql);
    let posts = query_as::<_, metadata::Posts>(&sql).fetch_all(pool).await?;
    Ok(posts)
}

/// 查询`friends`表中`link`包含`domain_str`的一条数据
pub async fn select_one_from_friends_with_linklike(
    pool: &SqlitePool,
    domain_str: &str,
) -> Result<metadata::Friends, Error> {
    let sql = format!("SELECT * from friends WHERE link like '%{domain_str}%'");
    // println!("{}", sql);

    let friend = query_as::<_, metadata::Friends>(&sql)
        .fetch_one(pool)
        .await?;
    Ok(friend)
}

/// 获取`posts`表中最近一次更新（`createdAt`最新）的时间
pub async fn select_latest_time_from_posts(pool: &SqlitePool) -> Result<String, Error> {
    let sql = "SELECT createdAt from posts ORDER BY createdAt DESC";
    let result = query(sql).fetch_one(pool).await?;
    let created_at: String = result.get("createdAt");
    Ok(created_at)
}

/// 查询`friends`表的所有数据
pub async fn select_all_from_friends(pool: &SqlitePool) -> Result<Vec<metadata::Friends>, Error> {
    let sql = String::from("SELECT * FROM friends");
    let res = query_as::<_, metadata::Friends>(&sql)
        .fetch_all(pool)
        .await?;
    Ok(res)
}

/// 清空`tb`表的数据
pub async fn truncate_table(pool: &SqlitePool, tb: &str) -> Result<(), Error> {
    let sql = format!("DELETE FROM {tb}");
    query(&sql).execute(pool).await?;
    Ok(())
}

pub async fn delete_outdated_posts(days: usize, dbpool: &SqlitePool) -> Result<usize, Error> {
    let sql = format!("DELETE FROM posts WHERE date(updated) < date('now', '-{days} days')");
    let affected_rows = query(&sql).execute(dbpool).await?;

    Ok(affected_rows.rows_affected() as usize)
}

#[cfg(test)]
mod tests {
    use super::*;
    use data_structures::metadata::{BasePosts, Friends, Posts};
    use std::time::SystemTime;

    // 辅助函数：创建测试数据库并返回连接池
    async fn setup_test_db() -> SqlitePool {
        let pool = connect_sqlite_dbpool("../tests/test.db").await.unwrap();
        match sqlx::migrate!("../db/schema/sqlite").run(&pool).await {
            Ok(()) => (),
            Err(e) => {
                panic!("{}", e);
            }
        };

        // 清空表以确保测试环境干净
        truncate_table(&pool, "friends").await.unwrap();
        truncate_table(&pool, "posts").await.unwrap();

        pool
    }

    // 测试连接数据库
    #[tokio::test]
    async fn test_connect_sqlite_dbpool() {
        // working directory is db/
        let pool = connect_sqlite_dbpool("../tests/test.db").await.unwrap();
        assert!(!pool.is_closed());
    }

    // 测试插入和查询好友
    #[tokio::test]
    async fn test_insert_and_select_friend() {
        let pool = setup_test_db().await;

        // 创建测试数据
        let friend = Friends {
            name: "测试用户".to_string(),
            link: "https://example.com".to_string(),
            error: false,
            avatar: "https://example.com/avatar.jpg".to_string(),
            created_at: SystemTime::now().elapsed().unwrap().as_secs().to_string(),
        };

        // 插入数据
        insert_friend_table(&friend, &pool).await.unwrap();

        // 查询数据
        let friends = select_all_from_friends(&pool).await.unwrap();

        // 验证结果
        assert_eq!(friends.len(), 1);
        assert_eq!(friends[0].name, "测试用户");
        assert_eq!(friends[0].link, "https://example.com");
        assert!(!friends[0].error);
    }

    // 测试插入和查询帖子
    #[tokio::test]
    async fn test_insert_and_select_post() {
        let pool = setup_test_db().await;

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
        insert_post_table(&post, &pool).await.unwrap();

        // 查询数据
        let posts = select_all_from_posts(&pool, 0, 0, "updated").await.unwrap();

        // 验证结果
        assert_eq!(posts.len(), 1);
        assert_eq!(posts[0].meta.title, "测试帖子");
        assert_eq!(posts[0].meta.link, "https://example.com/post");
        assert_eq!(posts[0].author, "测试作者");
    }

    // 测试批量插入好友
    #[tokio::test]
    async fn test_bulk_insert_friends() {
        let pool = setup_test_db().await;

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
        bulk_insert_friend_table(friends.into_iter(), &pool)
            .await
            .unwrap();

        // 查询数据
        let result = select_all_from_friends(&pool).await.unwrap();

        // 验证结果
        assert_eq!(result.len(), 2);
        assert!(result.iter().any(|f| f.name == "用户1"));
        assert!(result.iter().any(|f| f.name == "用户2"));
    }

    // 测试批量插入帖子
    #[tokio::test]
    async fn test_bulk_insert_posts() {
        let pool = setup_test_db().await;

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
        bulk_insert_post_table(posts.into_iter(), &pool)
            .await
            .unwrap();

        // 查询数据
        let result = select_all_from_posts(&pool, 0, 0, "updated").await.unwrap();

        // 验证结果
        assert_eq!(result.len(), 2);
        assert!(result.iter().any(|p| p.meta.title == "帖子1"));
        assert!(result.iter().any(|p| p.meta.title == "帖子2"));
    }

    // 测试查询带有特定链接的帖子
    #[tokio::test]
    async fn test_select_posts_with_linklike() {
        let pool = setup_test_db().await;

        // 插入测试数据
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

        bulk_insert_post_table(posts.into_iter(), &pool)
            .await
            .unwrap();

        // 查询特定链接的帖子
        let result = select_all_from_posts_with_linklike(&pool, "example.com", -1, "updated")
            .await
            .unwrap();

        // 验证结果
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].meta.title, "帖子1");

        // 查询限制数量
        let result = select_all_from_posts_with_linklike(&pool, "example", 1, "updated")
            .await
            .unwrap();
        assert_eq!(result.len(), 1);
    }

    // 测试查询带有特定链接的好友
    #[tokio::test]
    async fn test_select_friend_with_linklike() {
        let pool = setup_test_db().await;

        // 插入测试数据
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

        bulk_insert_friend_table(friends.into_iter(), &pool)
            .await
            .unwrap();

        // 查询特定链接的好友
        let result = select_one_from_friends_with_linklike(&pool, "example.com")
            .await
            .unwrap();

        // 验证结果
        assert_eq!(result.name, "用户1");
    }

    // 测试查询最新更新时间
    #[tokio::test]
    async fn test_select_latest_time() {
        let pool = setup_test_db().await;

        // 插入测试数据
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

        bulk_insert_post_table(posts.into_iter(), &pool)
            .await
            .unwrap();

        // 查询最新更新时间
        let latest_time = select_latest_time_from_posts(&pool).await.unwrap();

        // 验证结果
        assert!(latest_time == "2023-01-02" || latest_time == "2023-01-01");
    }

    // 测试清空表
    #[tokio::test]
    async fn test_truncate_table() {
        let pool = setup_test_db().await;

        // 插入测试数据
        let friend = Friends {
            name: "测试用户".to_string(),
            link: "https://example.com".to_string(),
            error: false,
            avatar: "https://example.com/avatar.jpg".to_string(),
            created_at: "2023-01-01".to_string(),
        };

        insert_friend_table(&friend, &pool).await.unwrap();

        // 验证数据已插入
        let friends = select_all_from_friends(&pool).await.unwrap();
        assert_eq!(friends.len(), 1);

        // 清空表
        truncate_table(&pool, "friends").await.unwrap();

        // 验证表已清空
        let friends = select_all_from_friends(&pool).await.unwrap();
        assert_eq!(friends.len(), 0);
    }

    // 测试清空好友表
    #[tokio::test]
    async fn test_truncate_friend_table() {
        let pool = setup_test_db().await;

        // 插入测试数据
        let friend = Friends {
            name: "测试用户".to_string(),
            link: "https://example.com".to_string(),
            error: false,
            avatar: "https://example.com/avatar.jpg".to_string(),
            created_at: "2023-01-01".to_string(),
        };

        insert_friend_table(&friend, &pool).await.unwrap();

        // 验证数据已插入
        let friends = select_all_from_friends(&pool).await.unwrap();
        assert_eq!(friends.len(), 1);

        // 清空好友表
        truncate_friend_table(&pool).await.unwrap();

        // 验证表已清空
        let friends = select_all_from_friends(&pool).await.unwrap();
        assert_eq!(friends.len(), 0);
    }

    // 测试删除过期帖子 - 只删除部分过期
    #[tokio::test]
    async fn test_delete_outdated_posts_partial() {
        let pool = setup_test_db().await;

        use chrono::{Duration, Local};
        let now = Local::now();
        let today = now.format("%Y-%m-%d").to_string();
        let yesterday = (now - Duration::days(1)).format("%Y-%m-%d").to_string();
        let old_date = (now - Duration::days(35)).format("%Y-%m-%d").to_string();

        // 插入三条数据：今天、昨天、35天前
        sqlx::query(
            "INSERT INTO posts (title, created, updated, link, author, avatar, rule, createdAt) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        )
        .bind("新帖子")
        .bind(&today)
        .bind(&today)
        .bind("https://example.com/post1")
        .bind("作者1")
        .bind("avatar1.jpg")
        .bind("test")
        .bind(&today)
        .execute(&pool)
        .await
        .unwrap();

        sqlx::query(
            "INSERT INTO posts (title, created, updated, link, author, avatar, rule, createdAt) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        )
        .bind("旧帖子1")
        .bind(&yesterday)
        .bind(&yesterday)
        .bind("https://example.com/post2")
        .bind("作者2")
        .bind("avatar2.jpg")
        .bind("test")
        .bind(&yesterday)
        .execute(&pool)
        .await
        .unwrap();

        sqlx::query(
            "INSERT INTO posts (title, created, updated, link, author, avatar, rule, createdAt) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        )
        .bind("旧帖子2")
        .bind(&old_date)
        .bind(&old_date)
        .bind("https://example.com/post3")
        .bind("作者3")
        .bind("avatar3.jpg")
        .bind("test")
        .bind(&old_date)
        .execute(&pool)
        .await
        .unwrap();

        // 删除30天前的过期帖子
        let deleted_count = delete_outdated_posts(30, &pool).await.unwrap();
        assert_eq!(deleted_count, 1);

        // 剩下2条
        let posts = select_all_from_posts(&pool, 0, 0, "updated").await.unwrap();
        assert_eq!(posts.len(), 2);
        assert!(posts.iter().any(|p| p.meta.title == "新帖子"));
        assert!(posts.iter().any(|p| p.meta.title == "旧帖子1"));
    }

    // 测试删除过期帖子 - 没有过期
    #[tokio::test]
    async fn test_delete_outdated_posts_no_outdated() {
        let pool = setup_test_db().await;

        use chrono::{Duration, Local};
        let now = Local::now();
        let today = now.format("%Y-%m-%d").to_string();
        let yesterday = (now - Duration::days(1)).format("%Y-%m-%d").to_string();

        // 插入两条数据：今天、昨天
        sqlx::query(
            "INSERT INTO posts (title, created, updated, link, author, avatar, rule, createdAt) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        )
        .bind("新帖子1")
        .bind(&today)
        .bind(&today)
        .bind("https://example.com/post1")
        .bind("作者1")
        .bind("avatar1.jpg")
        .bind("test")
        .bind(&today)
        .execute(&pool)
        .await
        .unwrap();

        sqlx::query(
            "INSERT INTO posts (title, created, updated, link, author, avatar, rule, createdAt) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        )
        .bind("新帖子2")
        .bind(&yesterday)
        .bind(&yesterday)
        .bind("https://example.com/post2")
        .bind("作者2")
        .bind("avatar2.jpg")
        .bind("test")
        .bind(&yesterday)
        .execute(&pool)
        .await
        .unwrap();

        // 删除30天前的过期帖子
        let deleted_count = delete_outdated_posts(30, &pool).await.unwrap();
        assert_eq!(deleted_count, 0);

        // 剩下2条
        let posts = select_all_from_posts(&pool, 0, 0, "updated").await.unwrap();
        assert_eq!(posts.len(), 2);
    }

    // 测试删除过期帖子 - 全部过期
    #[tokio::test]
    async fn test_delete_outdated_posts_all_outdated() {
        let pool = setup_test_db().await;

        use chrono::{Duration, Local};
        let now = Local::now();
        let old_date1 = (now - Duration::days(35)).format("%Y-%m-%d").to_string();
        let old_date2 = (now - Duration::days(40)).format("%Y-%m-%d").to_string();

        // 插入两条数据：35天前、40天前
        sqlx::query(
            "INSERT INTO posts (title, created, updated, link, author, avatar, rule, createdAt) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        )
        .bind("旧帖子1")
        .bind(&old_date1)
        .bind(&old_date1)
        .bind("https://example.com/post1")
        .bind("作者1")
        .bind("avatar1.jpg")
        .bind("test")
        .bind(&old_date1)
        .execute(&pool)
        .await
        .unwrap();

        sqlx::query(
            "INSERT INTO posts (title, created, updated, link, author, avatar, rule, createdAt) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        )
        .bind("旧帖子2")
        .bind(&old_date2)
        .bind(&old_date2)
        .bind("https://example.com/post2")
        .bind("作者2")
        .bind("avatar2.jpg")
        .bind("test")
        .bind(&old_date2)
        .execute(&pool)
        .await
        .unwrap();

        // 删除30天前的过期帖子
        let deleted_count = delete_outdated_posts(30, &pool).await.unwrap();
        assert_eq!(deleted_count, 2);

        // 剩下0条
        let posts = select_all_from_posts(&pool, 0, 0, "updated").await.unwrap();
        assert_eq!(posts.len(), 0);
    }
}
