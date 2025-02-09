import requests
from bs4 import BeautifulSoup

def get_article_links(url):
    article_links = []
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        #  ***  更新的选择器：使用 class_='ember-view' 的 div 元素  ***
        article_elements = soup.find_all('div', class_='ember-view') # <--- 需爬取页面链接的父层DIV class !!!
        for article_element in article_elements:
            link_tag = article_element.find('a') # 再次假设链接在 <a> 标签里
            if link_tag and link_tag.has_attr('href'):
                href = link_tag['href'] # 获取 <a> 标签的 href 属性值
                #  判断 href 是否为绝对 URL 或相对 URL
                if href.startswith("http"): # 如果是绝对 URL，直接使用
                    article_url = href
                else: # 如果是相对 URL，拼接成完整的 URL
                    article_url = "https://www.indiehackers.com" + href

                #  新增代码： 检查链接是否以 '/post/' 开头，并且是 indiehackers 域名下的
                if article_url.startswith("https://www.indiehackers.com/post/"):
                    article_links.append(article_url)
    else:
        print(f"Failed to fetch URL: {url}, status code: {response.status_code}")
    return article_links

def get_article_content(article_url):
    article_data = {} # 用字典存储文章数据
    response = requests.get(article_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # *** 请根据文章页面 HTML 结构修改以下选择器 ***
        title_tag = soup.find('h1', class_='post-title') #  示例：假设标题在 <h1 class="post-title"> 中
        content_tag = soup.find('div', class_='post-body') # 示例：假设正文在 <div class="post-body"> 中

        if title_tag:
            article_data['title'] = title_tag.text.strip() #  提取标题文本并去除首尾空格
        if content_tag:
            article_data['content'] = content_tag.text.strip() # 提取正文文本并去除首尾空格
        article_data['url'] = article_url #  保存文章 URL
    else:
        print(f"Failed to fetch article URL: {article_url}, status code: {response.status_code}")
    return article_data

start_url = "https://www.indiehackers.com/"
all_article_links = get_article_links(start_url)

if all_article_links:
    print(f"开始抓取 {len(all_article_links)} 篇文章内容...")
    articles_data = [] #  存储所有文章数据
    for link in all_article_links:
        article_data = get_article_content(link)
        if article_data: #  如果成功抓取到文章数据
            articles_data.append(article_data)

    print(f"成功抓取 {len(articles_data)} 篇文章内容。示例文章:")
    if articles_data:
        sample_article = articles_data[0] #  取第一篇文章作为示例
        print(f"  标题: {sample_article.get('title', 'N/A')}")
        print(f"  URL: {sample_article.get('url', 'N/A')}")
        # print(f"  内容 (前 200 字...): {sample_article.get('content', 'N/A')[:200]}...") # 可选，打印部分内容

else:
    print("没有抓取到文章链接，无法抓取文章内容。")