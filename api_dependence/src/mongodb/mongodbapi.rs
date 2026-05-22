use crate::format_response::PYQError;
use axum::{
    Json,
    extract::{Query, State},
};
use data_structures::query_params::{AllQueryParams, PostParams, RandomQueryParams};
use data_structures::{
    metadata::{Friends, Posts, SummaryResponse},
    response::{AllPostDataSomeFriend, AllPostDataWithSummary},
};
use db::{MongoDatabase, mongo};
use rand::prelude::*;
use url::Url;

pub async fn get_all(
    State(pool): State<MongoDatabase>,
    Query(params): Query<AllQueryParams>,
) -> Result<Json<AllPostDataWithSummary>, PYQError> {
    // println!("{:?}",params);
    let posts = match mongo::select_all_from_posts_with_summary(
        &pool,
        params.start.unwrap_or(0),
        params.end.unwrap_or(0),
        &params.sort_rule.unwrap_or(String::from("updated")),
    )
    .await
    {
        Ok(v) => v,
        Err(e) => return Err(PYQError::QueryDataBaseError(e.to_string())),
    };

    let last_updated_time = match mongo::select_latest_time_from_posts(&pool).await {
        Ok(v) => v,
        Err(e) => return Err(PYQError::QueryDataBaseError(e.to_string())),
    };

    let friends = match mongo::select_all_from_friends(&pool).await {
        Ok(v) => v,
        Err(e) => return Err(PYQError::QueryDataBaseError(e.to_string())),
    };
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
    let data = AllPostDataWithSummary::new(
        friends_num,
        active_num,
        lost_num,
        posts.len(),
        last_updated_time,
        posts,
        params.start.unwrap_or(0),
    );
    Ok(Json(data))
}

pub async fn get_friend(State(pool): State<MongoDatabase>) -> Result<Json<Vec<Friends>>, PYQError> {
    let friends = match mongo::select_all_from_friends(&pool).await {
        Ok(v) => v,
        Err(e) => return Err(PYQError::QueryDataBaseError(e.to_string())),
    };

    Ok(Json(friends))
}

pub async fn get_post(
    State(pool): State<MongoDatabase>,
    Query(params): Query<PostParams>,
) -> Result<Json<AllPostDataSomeFriend>, PYQError> {
    let (friend, search_domain) = match params.link {
        Some(link) => {
            let domain_str = match Url::parse(&link) {
                Ok(v) => match v.host_str() {
                    Some(host) => host.to_string(),
                    None => return Err(PYQError::QueryParamsError(String::from("无法解析出host"))),
                },
                Err(e) => return Err(PYQError::QueryParamsError(e.to_string())),
            };

            // 先尝试在 friends 表中查找
            match mongo::select_one_from_friends_with_linklike(&pool, &domain_str).await {
                Ok(v) => (v, domain_str),
                Err(_) => {
                    // friends 表中找不到（可能是换域名了），尝试用域名直接匹配 posts 表
                    let posts = match mongo::select_all_from_posts_with_linklike(
                        &pool,
                        &domain_str,
                        1,
                        "created",
                    )
                    .await
                    {
                        Ok(v) if !v.is_empty() => v,
                        _ => {
                            return Err(PYQError::QueryDataBaseError(format!(
                                "未找到域名 {} 对应的友链或文章",
                                domain_str
                            )));
                        }
                    };
                    // 通过 posts 中的 author 名字找到对应的 friend
                    let author = &posts[0].author;
                    let friends = match mongo::select_all_from_friends(&pool).await {
                        Ok(v) => v,
                        Err(e) => return Err(PYQError::QueryDataBaseError(e.to_string())),
                    };
                    match friends.into_iter().find(|f| &f.name == author) {
                        Some(f) => (f, domain_str),
                        None => {
                            return Err(PYQError::QueryDataBaseError(format!(
                                "未找到域名 {} 对应的友链",
                                domain_str
                            )));
                        }
                    }
                }
            }
        }
        None => {
            // 没有提供link，则随机获取一个friend
            let friends = match mongo::select_all_from_friends(&pool).await {
                Ok(v) => v,
                Err(e) => return Err(PYQError::QueryDataBaseError(e.to_string())),
            };
            let mut rng = rand::rng();
            match friends.choose(&mut rng).cloned() {
                Some(f) => {
                    let domain = match Url::parse(&f.link) {
                        Ok(v) => v.host_str().unwrap_or_default().to_string(),
                        Err(_) => f.link.clone(),
                    };
                    (f, domain)
                }
                None => {
                    return Err(PYQError::QueryDataBaseError(String::from(
                        "friends表数据为空",
                    )));
                }
            }
        }
    };
    // 使用域名匹配 posts 表，而不是完整的 friend.link URL
    let sort_rule = params.sort_rule.unwrap_or(String::from("created"));
    let num = params.num.unwrap_or(-1);
    let posts = match mongo::select_all_from_posts_with_linklike(
        &pool,
        &search_domain,
        num,
        &sort_rule,
    )
    .await
    {
        Ok(v) => v,
        Err(e) => return Err(PYQError::QueryDataBaseError(e.to_string())),
    };

    // 如果域名匹配不到文章（可能站点换了域名），用 author 名字匹配
    let posts = if posts.is_empty() {
        match mongo::select_posts_by_author(
            &pool,
            &friend.name,
            num,
            &sort_rule,
        )
        .await
        {
            Ok(v) => v,
            Err(_) => posts,
        }
    } else {
        posts
    };
    let data = AllPostDataSomeFriend::new(
        friend.name,
        friend.link,
        friend.avatar,
        posts.len(),
        posts,
        0,
    );
    Ok(Json(data))
}

pub async fn get_randomfriend(
    State(pool): State<MongoDatabase>,
    Query(params): Query<RandomQueryParams>,
) -> Result<Json<Vec<Friends>>, PYQError> {
    let friends = match mongo::select_all_from_friends(&pool).await {
        Ok(v) => v,
        Err(e) => return Err(PYQError::QueryDataBaseError(e.to_string())),
    };
    // println!("{:?}",params);
    let mut rng = rand::rng();
    let result: Vec<Friends> = friends
        .choose_multiple(&mut rng, params.num.unwrap_or(1))
        .cloned()
        .collect();
    Ok(Json(result))
}

pub async fn get_randompost(
    State(pool): State<MongoDatabase>,
    Query(params): Query<RandomQueryParams>,
) -> Result<Json<Vec<Posts>>, PYQError> {
    let posts = match mongo::select_all_from_posts(&pool, 0, 0, "updated").await {
        Ok(v) => v,
        Err(e) => return Err(PYQError::QueryDataBaseError(e.to_string())),
    };
    let mut rng = rand::rng();
    let result: Vec<Posts> = posts
        .choose_multiple(&mut rng, params.num.unwrap_or(1))
        .cloned()
        .collect();
    Ok(Json(result))
}

/// 查询参数：摘要查询
#[derive(serde::Deserialize)]
pub struct SummaryQueryParams {
    pub link: Option<String>,
}

/// 根据链接查询文章摘要
pub async fn get_summary(
    State(pool): State<MongoDatabase>,
    Query(params): Query<SummaryQueryParams>,
) -> Result<Json<SummaryResponse>, crate::format_response::PYQError> {
    let link = params.link.ok_or_else(|| {
        crate::format_response::PYQError::ParamError("param 'link' is required".to_string())
    })?;

    match mongo::select_article_summary_by_link(&link, &pool).await {
        Ok(Some(summary)) => {
            let response = SummaryResponse::from_article_summary(summary);
            Ok(Json(response))
        }
        Ok(None) => Err(crate::format_response::PYQError::NotFoundError(
            "not found".to_string(),
        )),
        Err(e) => Err(crate::format_response::PYQError::QueryDataBaseError(
            e.to_string(),
        )),
    }
}
