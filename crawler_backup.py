import requests
from bs4 import BeautifulSoup

def get_article_links(url):
    article_links = []
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # ***  请根据你在浏览器开发者工具中分析的结果，修改以下选择器  ***
        article_elements = soup.find_all('div', class_='ember-view') #  <--- 示例选择器，需要修改 !!!
        for article_element in article_elements:
            link_tag = article_element.find('a') #  再次假设链接在 <a> 标签里
            if link_tag and link_tag.has_attr('href'):
                article_url = "https://www.indiehackers.com" + link_tag['href'] #  拼接成完整的 URL
                article_links.append(article_url)
    else:
        print(f"Failed to fetch URL: {url}, status code: {response.status_code}")
    return article_links

start_url = "https://www.indiehackers.com/"
all_article_links = get_article_links(start_url)

if all_article_links:
    print(f"抓取到 {len(all_article_links)} 篇文章链接:")
    for link in all_article_links:
        print(link) # 打印抓取到的文章链接
else:
    print("没有抓取到文章链接。请检查选择器是否正确。")
