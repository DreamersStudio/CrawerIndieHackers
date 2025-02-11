import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from notion_client import Client as NotionClient
#from feishu_sdk import FeishuClient
import time
from datetime import datetime, timezone
import json
import logging
from urllib3 import disable_warnings, exceptions as urllib3_exceptions

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 禁用 SSL 警告
disable_warnings(urllib3_exceptions.InsecureRequestWarning)

# 初始化翻译器
translator = GoogleTranslator(source='en', target='zh-CN')

# 初始化 Notion 客户端
notion = NotionClient(auth="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")  # 替换为你的 Notion 认证令牌
notion_database_id = "1967cf875dc4802b8fa6ce998b327b97"  # 替换为你的 Notion 数据库 ID

# 初始化飞书客户端
#feishu = FeishuClient(app_id="your-feishu-app-id", app_secret="your-feishu-app-secret")

def save_articles(articles_data, filename='articles.json'):
    """保存文章到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)
        logging.info(f"文章已保存到 {filename}")
    except Exception as e:
        logging.error(f"保存文章失败: {str(e)}")

def get_article_links(url, max_retries=3):
    article_links = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    for attempt in range(max_retries):
        try:
            logging.info(f"正在尝试第 {attempt + 1} 次连接...")
            response = session.get(url, verify=True, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                article_elements = soup.find_all('div', class_='ember-view')
                
                for article_element in article_elements:
                    if article_element.find(string='IH+ Subscribers Only'):
                        continue
                        
                    link_tag = article_element.find('a', href=True)
                    if link_tag and '/post/' in link_tag['href']:
                        href = link_tag['href']
                        article_url = href if href.startswith("http") else f"https://www.indiehackers.com{href}"
                        if article_url not in article_links:
                            article_links.append(article_url)
                
                return article_links
            else:
                logging.warning(f"服务器返回状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"尝试 {attempt + 1} 失败: {str(e)}")
            if attempt < max_retries - 1:
                logging.info("等待后重试...")
                time.sleep(2)
    
    return article_links

def get_article_content(article_url, max_retries=3):
    article_data = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    for attempt in range(max_retries):
        try:
            response = session.get(article_url, verify=True, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if soup.find(string='IH+ Subscribers Only'):
                    logging.info(f"跳过付费文章: {article_url}")
                    return None
                
                title_selectors = [
                    'h1.firestore-post__title',
                    'h1.post-title',
                    'h1.post-page__title',
                    'h1.post-page__header',
                    'div.post-header h1',
                    'header.post-page__title',
                    'article h1'
                ]
                
                content_selectors = [
                    'div.firestore-post__main',
                    'div.post-content',
                    'div.post-page__body',
                    'div.post-page__main',
                    'article div.content'
                ]
                
                title = next((tag.text.strip() for tag in (soup.select_one(selector) for selector in title_selectors) if tag and tag.text.strip()), None)
                content = next((tag.text.strip() for tag in (soup.select_one(selector) for selector in content_selectors) if tag and tag.text.strip()), None)
                
                if not title:
                    logging.warning(f"无法找到文章标题: {article_url}")
                    title = article_url.split('/post/')[-1].replace('-', ' ').title()
                
                article_data['title'] = title
                article_data['content'] = content if content else "No content found"
                article_data['url'] = article_url
                article_data['crawl_time'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                
                if not content:
                    logging.warning(f"无法找到文章内容，URL: {article_url}")
                    logging.debug("页面结构:")
                    logging.debug(soup.prettify()[:500])  # 只打印前500个字符
                
                return article_data
                
        except requests.exceptions.RequestException as e:
            logging.error(f"获取文章内容失败 ({attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return article_data

def translate_article_content(content):
    try:
        translated = translator.translate(content)
        return translated
    except Exception as e:
        logging.error(f"翻译失败: {str(e)} - 内容: {content[:100]}...")  # 记录部分内容以便调试
        return content

def save_to_notion(article_data):
    try:
        # 截断内容以符合 Notion 的限制
        translated_content = article_data['translated_content']
        if len(translated_content) > 2000:
            translated_content = translated_content[:2000] + "..."
        
        page = notion.pages.create(
            parent={"database_id": notion_database_id},
            properties={
                "Name": {"title": [{"text": {"content": article_data['title']}}]},  # 确保属性名称正确
                "URL": {"url": article_data['url']},
                "Crawl Time": {"date": {"start": article_data['crawl_time']}},
                "Category": {"select": {"name": article_data['category']}},
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": translated_content}}],
                    },
                }
            ],
        )
        logging.info(f"文章已保存到 Notion: {page['id']}")
    except Exception as e:
        logging.error(f"保存到 Notion 失败: {str(e)}")

"""
def save_to_feishu(article_data):
    try:
        response = feishu.create_document(
            title=article_data['title'],
            content=article_data['translated_content'],
            url=article_data['url'],
            crawl_time=article_data['crawl_time'],
            category=article_data['category']
        )
        logging.info(f"文章已保存到飞书: {response['data']['doc_id']}")
    except Exception as e:
        logging.error(f"保存到飞书失败: {str(e)}")
"""

def classify_article(content):
    keywords = {
        "技术": ["技术", "开发", "编程", "软件"],
        "产品": ["产品", "设计", "用户体验", "UI"],
        "创业": ["创业", "初创", "商业模式", "融资"],
        "市场": ["市场", "营销", "广告", "用户获取"],
        "其他": []
    }
    
    for category, words in keywords.items():
        for word in words:
            if word in content:
                return category
    return "其他"

def main():
    start_url = "https://www.indiehackers.com/"
    logging.info("开始抓取文章链接...")
    
    all_article_links = get_article_links(start_url)
    
    if all_article_links:
        logging.info(f"找到 {len(all_article_links)} 篇文章链接")
        articles_data = []
        skipped_count = 0
        failed_urls = []
        
        for i, link in enumerate(all_article_links, 1):
            logging.info(f"\n正在抓取第 {i}/{len(all_article_links)} 篇文章...")
            logging.info(f"URL: {link}")
            
            article_data = get_article_content(link)
            
            if article_data and article_data.get('title'):
                translated_content = translate_article_content(article_data['content'])
                article_data['translated_content'] = translated_content
                article_data['category'] = classify_article(translated_content)
                
                # 保存到 Notion
                save_to_notion(article_data)
                
                # 保存到飞书
                #save_to_feishu(article_data)
                
                articles_data.append(article_data)
                logging.info(f"成功抓取: {article_data['title']}")
            elif article_data is None:
                skipped_count += 1
                logging.info(f"跳过第 {i} 篇文章 (付费内容)")
            else:
                failed_urls.append(link)
                logging.warning(f"警告: 抓取失败 - {link}")
            
            time.sleep(1)
        
        logging.info("\n抓取完成:")
        logging.info(f"- 成功抓取: {len(articles_data)} 篇")
        logging.info(f"- 跳过付费文章: {skipped_count} 篇")
        logging.info(f"- 抓取失败: {len(failed_urls)} 篇")
        
        if failed_urls:
            logging.warning("\n失败的URL:")
            for url in failed_urls:
                logging.warning(url)
        
        if articles_data:
            # 保存文章到JSON文件
            save_articles(articles_data)
            
            # 显示示例文章
            sample_article = articles_data[0]
            logging.info("\n示例文章:")
            logging.info(f"标题: {sample_article.get('title', 'N/A')}")
            logging.info(f"URL: {sample_article.get('url', 'N/A')}")
            logging.info(f"内容长度: {len(sample_article.get('content', ''))}")
    else:
        logging.info("未找到任何文章链接")

if __name__ == "__main__":
    main()