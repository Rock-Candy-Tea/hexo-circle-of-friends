pub mod query_params {
    use serde::Deserialize;
    #[derive(Debug, Deserialize)]
    pub struct AllQueryParams {
        pub start: Option<usize>,
        pub end: Option<usize>,
        #[serde(rename(deserialize = "rule"))]
        pub sort_rule: Option<String>,
    }

    #[derive(Debug, Deserialize)]
    pub struct PostParams {
        pub link: Option<String>,
        pub num: Option<i32>,
        #[serde(rename(deserialize = "rule"))]
        pub sort_rule: Option<String>,
    }

    #[derive(Debug, Deserialize)]
    pub struct RandomQueryParams {
        pub num: Option<usize>,
    }
}

/// 包含基本数据结构定义
pub mod metadata {
    use serde::{Deserialize, Serialize};
    use sqlx::FromRow;

    /// 文章结构定义
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize, FromRow)]
    pub struct BasePosts {
        pub title: String,
        pub created: String,
        pub updated: String,
        pub link: String,
        // #[serde(skip_serializing)]
        // #[serde(default)]
        pub rule: String,
    }

    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize, FromRow)]
    pub struct Posts {
        #[sqlx(flatten)]
        #[serde(flatten)]
        pub meta: BasePosts,
        pub author: String,
        pub avatar: String,
        #[serde(rename = "createdAt")]
        #[sqlx(rename = "createdAt")]
        pub created_at: String,
    }

    impl BasePosts {
        pub fn new(
            title: String,
            created: String,
            updated: String,
            link: String,
            rule: String,
        ) -> BasePosts {
            BasePosts {
                title,
                created,
                updated,
                link,
                rule,
            }
        }
    }

    impl Posts {
        pub fn new(meta: BasePosts, author: String, avatar: String, created_at: String) -> Posts {
            Posts {
                meta,
                author,
                avatar,
                created_at,
            }
        }
    }

    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize, FromRow)]
    pub struct Friends {
        pub name: String,
        pub link: String,
        pub avatar: String,
        pub error: bool,
        #[serde(rename = "createdAt")]
        #[sqlx(rename = "createdAt")]
        pub created_at: String,
    }

    impl Friends {
        pub fn new(
            name: String,
            link: String,
            avatar: String,
            error: bool,
            created_at: String,
        ) -> Friends {
            Friends {
                name,
                link,
                avatar,
                error,
                created_at,
            }
        }
    }
}

/// 配置
pub mod config {
    use serde::{Deserialize, Serialize};
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct LinkMeta {
        pub link: String,
        pub theme: String,
    }
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct SettingsFriendsLinksMeta {
        pub enable: bool,
        pub json_api: String,
        pub list: Vec<Vec<String>>,
    }

    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct Settings {
        #[serde(rename = "LINK")]
        pub link: Vec<LinkMeta>,
        #[serde(rename = "SETTINGS_FRIENDS_LINKS")]
        pub settings_friends_links: SettingsFriendsLinksMeta,
        #[serde(rename = "BLOCK_SITE")]
        pub block_site: Vec<String>,
        #[serde(rename = "MAX_POSTS_NUM")]
        pub max_posts_num: usize,
        #[serde(rename = "OUTDATE_CLEAN")]
        pub outdate_clean: usize,
        #[serde(rename = "DATABASE")]
        pub database: String,
        #[serde(rename = "DEPLOY_TYPE")]
        pub deploy_type: String,
        #[serde(rename = "SIMPLE_MODE")]
        pub simple_mode: bool,
        #[serde(rename = "CRON")]
        pub cron: String,
    }
}

/// 响应
pub mod response {
    use super::metadata::*;
    use serde::{Deserialize, Serialize};

    /// 统计数据
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct StatisticalData {
        friends_num: usize,
        active_num: usize,
        error_num: usize,
        article_num: usize,
        last_updated_time: String,
    }
    impl StatisticalData {
        fn new(
            friends_num: usize,
            active_num: usize,
            error_num: usize,
            article_num: usize,
            last_updated_time: String,
        ) -> Self {
            StatisticalData {
                friends_num,
                active_num,
                error_num,
                article_num,
                last_updated_time,
            }
        }
    }

    /// 文章数据
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct ArticleData {
        // 排序
        floor: usize,
        title: String,
        created: String,
        updated: String,
        link: String,
        author: String,
        avatar: String,
    }

    impl ArticleData {
        fn new(
            floor: usize,
            title: String,
            created: String,
            updated: String,
            link: String,
            author: String,
            avatar: String,
        ) -> Self {
            ArticleData {
                floor,
                title,
                created,
                updated,
                link,
                author,
                avatar,
            }
        }
    }

    /// 所有文章数据
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct AllPostData {
        pub statistical_data: StatisticalData,
        pub article_data: Vec<ArticleData>,
    }

    impl AllPostData {
        pub fn new(
            friends_num: usize,
            active_num: usize,
            error_num: usize,
            article_num: usize,
            last_updated_time: String,
            posts: Vec<Posts>,
            start_offset: usize, // 用于计算floor
        ) -> AllPostData {
            let article_data: Vec<ArticleData> = posts
                .into_iter()
                .enumerate()
                .map(|(floor, posts)| {
                    ArticleData::new(
                        floor + start_offset + 1,
                        posts.meta.title,
                        posts.meta.created,
                        posts.meta.updated,
                        posts.meta.link,
                        posts.author,
                        posts.avatar,
                    )
                })
                .collect();
            AllPostData {
                statistical_data: StatisticalData::new(
                    friends_num,
                    active_num,
                    error_num,
                    article_num,
                    last_updated_time,
                ),
                article_data,
            }
        }
    }

    /// 某个friend的统计数据
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct StatisticalDataOfSomeFriend {
        name: String,
        link: String,
        avatar: String,
        article_num: usize,
    }
    impl StatisticalDataOfSomeFriend {
        pub fn new(name: String, link: String, avatar: String, article_num: usize) -> Self {
            StatisticalDataOfSomeFriend {
                name,
                link,
                avatar,
                article_num,
            }
        }
    }

    /// 某个friend的所有文章数据
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct AllPostDataSomeFriend {
        pub statistical_data: StatisticalDataOfSomeFriend,
        pub article_data: Vec<ArticleData>,
    }

    impl AllPostDataSomeFriend {
        pub fn new(
            name: String,
            link: String,
            avatar: String,
            article_num: usize,
            posts: Vec<Posts>,
            start_offset: usize, // 用于计算floor
        ) -> AllPostDataSomeFriend {
            let article_data: Vec<ArticleData> = posts
                .into_iter()
                .enumerate()
                .map(|(floor, posts)| {
                    ArticleData::new(
                        floor + start_offset + 1,
                        posts.meta.title,
                        posts.meta.created,
                        posts.meta.updated,
                        posts.meta.link,
                        posts.author,
                        posts.avatar,
                    )
                })
                .collect();
            AllPostDataSomeFriend {
                statistical_data: StatisticalDataOfSomeFriend::new(name, link, avatar, article_num),
                article_data,
            }
        }
    }
}
