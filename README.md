# 友链朋友圈

你是否经常烦恼于友链过多但没有时间浏览？那么友链朋友圈将解决这一痛点。你可以随时获取友链网站的更新内容，并了解友链的活跃情况 。

效果如下：

![](https://cdn.nlark.com/yuque/0/2021/png/8391485/1612877553087-3087b091-93ce-40fd-a49f-8baf0f0f49c4.png#align=left&display=inline&height=521&margin=%5Bobject%20Object%5D&name=image.png&originHeight=521&originWidth=386&size=161076&status=done&style=none&width=386)

```
目前 release 1.18 版本：
① 支持butterfly、volantis、matery主题的友链获取
② 支持小康友链及 volantis 主题友链，即部署于 gitee 上的 issuse 友链获取
③ 支持 butterfly、volantis、matery 主题的最新文章获取
④ 支持大部分拥有 sitemap 网站的文章获取
⑤ 拥有友链屏蔽、关键词屏蔽、等自定义 yaml 的配置项
⑥ 代码重构并规范化，便于二次开发

bug修复
① 重复爬取同一文章问题
```
预览链接：https://noionion.top/friendcircle/

教程请查阅：https://zfe.space/post/friend-link-circle.html

--------

# 开发者说明

## 主程序说明

业务流程：
主程序-->（处理器`handlers`）控件—->组件(`component`)

组件作为最底层，单向调用。
处理器可以调用组件，组件不可以调用处理里代码块。
避免产生双向调用执行流程不清。

处理器之间，不能互相调用。
避免出现处理器相互依赖，做到移除单一处理器时，不会导致其他处理器出错。
(特例：`coreSettings.py`，其他处理器可以单向调用`coreSettings.py`的值，
但`coreSettings.py`不能调用其他处理器的函数/类来处理)。
处理器避免直接调用外部`settings.py`里的参数，而是使用`coreSettings.py`来调用设置的值。
如要全局设置中的值，由`coreSettings.py`处理器统筹，使调用收束。

主程序只负责：
* 调用处理器；
* 程序的整体执行流程；
* 打印执行信息.

## 主题爬虫适配

请在`theme`文件夹处增添以主题名命名的`.py`文件，文件中至少包含以下两个函数：

### 友链爬取函数 get_friendlink(friendpage_link, friend_poor)

> 传入友链页面地址`friendpage`和友链列表`friend_poor`两个参数，无需返回值。
> 
> 对于爬取到的友链地址`user_info`中应带有如下几个值（有序）：`name`，`link`，`img/avatar`。格式如：`user_info = [name, link, img]`
> 
> 然后将其放入列表`frieng_poor`中：`friend_poor.append(user_info)`


### 最新文章爬取函数 get_last_post(user_info,post_poor)

> 传入友链信息列表`uesr_info`（格式如上）和文章列表`post_poor`两个参数，需返回值`error`，标记是否错误
> 
> 对于爬取到的文章信息`post_info`中应带有如下键值对：
? 
> ```PY
> post_info = {
>    'title':    , 
>     'time':     ,
>     'link':     ,
>     'name':     ,
>    'img':      
> }
> ```
> 
> 然后将其放入列表`post_poor`中：`post_poor.append(post_info)`

> **注意函数名，变量名保持一致，否则主函数将无法正确运行**

主函数部分只需导入对应的文件和增添对象即可，修改部分如下所示：

（示例即为当前版本适配）

```PY
# component
from theme import butterfly,matery,volantis

# theme fit massage
themes = [
    butterfly,
    matery,
    volantis
]
```

--------

## 开发者名单

| <img class="d-block avatar-user" src="https://avatars.githubusercontent.com/u/19563906?s=64&amp;v=4" width="64" height="64" alt="@Zfour"> | <img class="d-block avatar-user" src="https://avatars.githubusercontent.com/u/18726905?s=64&amp;v=4" width="64" height="64" alt="@DeSireFire"> | <img class="d-block avatar-user" src="https://avatars.githubusercontent.com/u/72645310?s=64&amp;v=4" width="64" height="64" alt="@2X-ercha"> |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| [Zfour](https://github.com/Zfour)                            | [RaXianch](https://github.com/DeSireFire)                    | [noionion](https://github.com/2X-ercha)                      |

--------

## star记录

![](https://starchart.cc/Rock-Candy-Tea/hexo-circle-of-friends.svg)

---------

## 相关

npm安装前端方案：参照 [Friend link subscription](https://akilar.top/posts/8480b91c/)

```BASH
npm install hexo-butterfly-fcircle --save
```




