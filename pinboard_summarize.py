#!/usr/bin/python3
import argparse
import os
import pinboard
import requests
import configparser
import json
from bs4 import BeautifulSoup
from html2text import HTML2Text
from openai import OpenAI

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0'
}
prompt = """
You are an expert on documentation writing and summarizing text. Create a one paragraph summary of the following text and provide a list of tags that can be used to categorize it. There should not be any spaces between tags. The text is from a website and will be used to provide a description of the website for a bookmark. ONLY respond with the output in the following JSON format:
  {
    "description": "YOUR SUMMARY",
    "tags": ["TAG 1", "TAG 2"]
  }"""

def get_website(url, headers=headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()


    soup = BeautifulSoup(response.text, 'html.parser')
    if soup.title is not None:
        title = soup.title.string
    else:
        raise ValueError("No title found")

    h = HTML2Text()
    h.ignore_links = True

    return title, h.handle(response.text)

def get_summary(text, openai_api_key, model="gpt-4-turbo"):
    client = OpenAI(api_key=openai_api_key)

    completion = client.chat.completions.create(
        temperature=0.2,
        top_p=.1,
         messages=[
        { "role": "system",
          "content": prompt
        },
        {
            "role": "user",
            "content": text,
        }
    ],
    model=model,
    )

    j = completion.choices[0].message.content
    if j is not None:
        return json.loads(j)
    else:
        raise ValueError("No summary found")

def add_bookmark(description, tags, title, url, api_token):
  pb = pinboard.Pinboard(api_token)
  pb.posts.add(description=title, extended=description, tags=tags, url=url)


def main():
    parser = argparse.ArgumentParser(description='Print URL in brackets.')
    parser.add_argument('url', help='URL to be printed in brackets')

    args = parser.parse_args()

    config = configparser.ConfigParser()
    ini_file_path = os.path.expanduser('~/.config/pinboard-summarize/config.ini')
    config.read(ini_file_path)
    pinboard_api_key = config['authentication']['pinboard']
    openai_api_key = config['authentication']['openai']

    title, text = get_website(args.url)
    summary = get_summary(text, openai_api_key)
    success = add_bookmark(summary['description'], summary['tags'], title, args.url, pinboard_api_key)
    if success is not None:
        raise ValueError(f"Bookmark not added: {success}")

if __name__ == "__main__":
    main()
