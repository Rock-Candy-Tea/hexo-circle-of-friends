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

    /// 包含摘要信息的文章结构体，用于API响应
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct PostsWithSummary {
        #[serde(flatten)]
        pub meta: BasePosts,
        pub author: String,
        pub avatar: String,
        #[serde(rename = "createdAt")]
        pub created_at: String,
        // 摘要相关字段（可选）
        pub summary: Option<String>,
        pub ai_model: Option<String>,
        pub summary_created_at: Option<String>,
        pub summary_updated_at: Option<String>,
    }

    impl PostsWithSummary {
        #[allow(clippy::too_many_arguments)]
        pub fn new(
            meta: BasePosts,
            author: String,
            avatar: String,
            created_at: String,
            summary: Option<String>,
            ai_model: Option<String>,
            summary_created_at: Option<String>,
            summary_updated_at: Option<String>,
        ) -> PostsWithSummary {
            PostsWithSummary {
                meta,
                author,
                avatar,
                created_at,
                summary,
                ai_model,
                summary_created_at,
                summary_updated_at,
            }
        }

        /// 从Posts转换，不包含摘要信息
        pub fn from_posts(posts: Posts) -> PostsWithSummary {
            PostsWithSummary {
                meta: posts.meta,
                author: posts.author,
                avatar: posts.avatar,
                created_at: posts.created_at,
                summary: None,
                ai_model: None,
                summary_created_at: None,
                summary_updated_at: None,
            }
        }
    }

    /// 文章摘要查询响应结构体
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct SummaryResponse {
        pub link: String,
        pub summary: Option<String>,
        pub ai_model: Option<String>,
        pub content_hash: String,
        pub created_at: String,
        pub updated_at: String,
    }

    impl SummaryResponse {
        pub fn new(
            link: String,
            summary: Option<String>,
            ai_model: Option<String>,
            content_hash: String,
            created_at: String,
            updated_at: String,
        ) -> SummaryResponse {
            SummaryResponse {
                link,
                summary,
                ai_model,
                content_hash,
                created_at,
                updated_at,
            }
        }

        pub fn from_article_summary(summary: ArticleSummary) -> SummaryResponse {
            SummaryResponse {
                link: summary.link,
                summary: Some(summary.summary),
                ai_model: summary.ai_model,
                content_hash: summary.content_hash,
                created_at: summary.created_at,
                updated_at: summary.updated_at,
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

    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize, FromRow)]
    pub struct ArticleSummary {
        pub link: String,
        pub content_hash: String,
        pub summary: String,
        pub ai_model: Option<String>,
        #[serde(rename = "createdAt")]
        #[sqlx(rename = "createdAt")]
        pub created_at: String,
        #[serde(rename = "updatedAt")]
        #[sqlx(rename = "updatedAt")]
        pub updated_at: String,
    }

    impl ArticleSummary {
        pub fn new(
            link: String,
            content_hash: String,
            summary: String,
            ai_model: Option<String>,
            created_at: String,
            updated_at: String,
        ) -> ArticleSummary {
            ArticleSummary {
                link,
                content_hash,
                summary,
                ai_model,
                created_at,
                updated_at,
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
        pub json_api_or_path: String,
        pub list: Vec<Vec<String>>,
    }

    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct SettingsFriendsLinksJsonMeta {
        pub friends: Vec<Vec<String>>,
    }

    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct GenerateSummaryConfig {
        pub enabled: bool,
        pub provider: String, // "gemini", "siliconflow", "bigmodel", or "all"
        pub max_concurrent: usize, // 默认: 3
        pub wait_on_rate_limit: bool, // 默认: true
        pub max_chars: usize, // 默认: 8000

        pub gemini: Option<ModelConfig>,
        pub siliconflow: Option<ModelConfig>,
        pub bigmodel: Option<ModelConfig>,
    }

    impl GenerateSummaryConfig {
        /// 获取最大并发数，如果未配置则返回默认值
        pub fn get_max_concurrent(&self) -> usize {
            self.max_concurrent
        }

        /// 获取是否等待限速，如果未配置则返回默认值
        pub fn get_wait_on_rate_limit(&self) -> bool {
            self.wait_on_rate_limit
        }

        /// 获取最大字符数，如果未配置则返回默认值
        pub fn get_max_chars(&self) -> usize {
            self.max_chars
        }

        /// 获取分块大小 (自动计算为 max_chars 的一半)
        pub fn get_chunk_size(&self) -> usize {
            self.get_max_chars() / 2
        }

        /// 获取重试次数 (智能默认值)
        pub fn get_retry_attempts(&self) -> usize {
            3
        }

        /// 获取限速等待时间 (智能默认值)
        pub fn get_rate_limit_delay(&self) -> u64 {
            60
        }
    }

    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct ModelConfig {
        pub models: Vec<String>,
    }

    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct Settings {
        #[serde(rename = "LINK")]
        pub link: Vec<LinkMeta>,
        #[serde(rename = "SETTINGS_FRIENDS_LINKS")]
        pub settings_friends_links: SettingsFriendsLinksMeta,
        #[serde(rename = "BLOCK_SITE")]
        pub block_site: Vec<String>,
        #[serde(rename = "BLOCK_SITE_REVERSE")]
        pub block_site_reverse: bool,
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
        #[serde(rename = "GENERATE_SUMMARY")]
        pub generate_summary: GenerateSummaryConfig,
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

    /// 包含摘要信息的文章数据
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct ArticleDataWithSummary {
        // 排序
        pub floor: usize,
        pub title: String,
        pub created: String,
        pub updated: String,
        pub link: String,
        pub author: String,
        pub avatar: String,
        // 摘要相关字段
        pub summary: Option<String>,
        pub ai_model: Option<String>,
        pub summary_created_at: Option<String>,
        pub summary_updated_at: Option<String>,
    }

    impl ArticleDataWithSummary {
        #[allow(clippy::too_many_arguments)]
        pub fn new(
            floor: usize,
            title: String,
            created: String,
            updated: String,
            link: String,
            author: String,
            avatar: String,
            summary: Option<String>,
            ai_model: Option<String>,
            summary_created_at: Option<String>,
            summary_updated_at: Option<String>,
        ) -> Self {
            ArticleDataWithSummary {
                floor,
                title,
                created,
                updated,
                link,
                author,
                avatar,
                summary,
                ai_model,
                summary_created_at,
                summary_updated_at,
            }
        }

        /// 从PostsWithSummary和floor构建
        pub fn from_posts_with_summary(posts: PostsWithSummary, floor: usize) -> Self {
            ArticleDataWithSummary {
                floor,
                title: posts.meta.title,
                created: posts.meta.created,
                updated: posts.meta.updated,
                link: posts.meta.link,
                author: posts.author,
                avatar: posts.avatar,
                summary: posts.summary,
                ai_model: posts.ai_model,
                summary_created_at: posts.summary_created_at,
                summary_updated_at: posts.summary_updated_at,
            }
        }
    }

    /// 所有文章数据
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct AllPostData {
        pub statistical_data: StatisticalData,
        pub article_data: Vec<ArticleData>,
    }

    /// 包含摘要信息的所有文章数据
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct AllPostDataWithSummary {
        pub statistical_data: StatisticalData,
        pub article_data: Vec<ArticleDataWithSummary>,
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

    impl AllPostDataWithSummary {
        pub fn new(
            friends_num: usize,
            active_num: usize,
            error_num: usize,
            article_num: usize,
            last_updated_time: String,
            posts: Vec<PostsWithSummary>,
            start_offset: usize, // 用于计算floor
        ) -> AllPostDataWithSummary {
            let article_data: Vec<ArticleDataWithSummary> = posts
                .into_iter()
                .enumerate()
                .map(|(floor, posts)| {
                    ArticleDataWithSummary::from_posts_with_summary(posts, floor + start_offset + 1)
                })
                .collect();
            AllPostDataWithSummary {
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

/// 版本检查相关数据结构
pub mod version {
    use serde::{Deserialize, Serialize};

    /// 简化的版本信息响应
    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct VersionResponse {
        /// 当前版本号
        pub version: String,
    }

    impl VersionResponse {
        pub fn new(version: String) -> Self {
            Self { version }
        }
    }
}

#[cfg(test)]
mod config_tests;
