# 友链朋友圈

你是否经常烦恼于友链过多但没有时间浏览？那么友链朋友圈将解决这一痛点。你可以随时获取友链网站的更新内容，并了解友链的活跃情况 。

部署教程：[文档](https://hexo-circle-of-friends-doc.vercel.app/) | [备用地址](https://hiltay.github.io/hexo-circle-of-friends-doc/)

⭐从4.1.3版本开始，一定要在配置项中配置友链页的获取策略
```
目前 release 4.1.5 版本：
- 支持 gitee 上的 issuse 友链获取
- 支持 github 上的 issuse 友链获取
- 支持 butterfly、volantis、matery、sakura、fluid主题的最新文章获取
- 新增目前最通用的atom和rss规则
- 支持站点屏蔽，在配置项选择开启
- 支持更新时间和创建时间排序
- 支持未适配的hexo主题和非hexo用户使用，在配置项选择开启配置项友链
- 支持爬取wordpress类型的博客
- 新增对nexmoe、Yun、stun主题的爬取
- 新增额外的友链页同时爬取，在配置项选择开启
- 新增对stellar主题的爬取
- 支持添加HTTP代理，在配置项选择开启
- 新增配置项友链选项，自定义订阅后缀
- 逻辑重构，新增友链页获取策略配置
- 添加数据存储配置，提供多种存储方式
- 将api整合到仓库
- 添加部署方式配置，可部署在本地服务端
- feed订阅解析更加精准了

bug修复：
- wordpress类型博客的时间格式问题
- butterfly主题友链页解析不再抓取背景图片了
- 修复了github和gitee对volantis主题的友链获取
- 屏蔽站点现在不计入失联数
- 修复了sakura主题和nexmoe主题偶尔报错的问题
- 现在可以获取Yun主题的外置JSON友链
- 优化了启动项配置
```






