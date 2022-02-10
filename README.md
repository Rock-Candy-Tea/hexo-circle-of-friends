# 友链朋友圈

你是否经常烦恼于友链过多但没有时间浏览？那么友链朋友圈将解决这一痛点。你可以随时获取友链网站的更新内容，并了解友链的活跃情况。

部署教程：[文档](https://hexo-circle-of-friends-doc.vercel.app/) | [备用地址](https://hiltay.github.io/hexo-circle-of-friends-doc/)

⭐从4.1.3版本开始，一定要在配置项中配置友链页的获取策略
```
目前 release 4.2.4 版本：
- 支持 gitee 和 github 上的 issuse 友链获取
- 支持butterfly、volantis、matery、sakura、fluid、nexmoe、Yun、stun、stellar主题的友链和文章获取
- 支持feed订阅规则，如atom、rss等规则（支持wordpress类型的博客）
- 支持自定义订阅后缀
- 支持站点屏蔽
- 支持按照更新时间和创建时间排序
- 支持未适配的hexo主题和非hexo用户使用，在配置项选择开启配置项友链
- 额外的友链页同时爬取
- 支持添加HTTP代理
- 新增数据存储配置，提供多种存储方式
- 新增部署方式配置，可部署在本地服务端
- 将api整合到主仓库
- 新增next四种主题的文章获取，与Yun规则合并，暂不支持友链页获取

bug修复：
- wordpress类型博客的时间格式问题
- butterfly主题友链页解析不再抓取背景图片了
- 修复了github和gitee对volantis主题的友链获取
- 屏蔽站点现在不计入失联数
- 修复了sakura主题和nexmoe主题偶尔报错的问题
- 现在可以获取Yun主题的外置JSON友链
- 优化了启动项配置
- feed订阅解析更加精准了
- 解决了docker和server定时任务运行爬虫报错的问题
- 文章超出当前时间的判断，逻辑优化与代码格式化
- 移除bs4依赖
- 移除旧订阅规则解析
- 修复butterfly的时间获取
```

