from splinter import Browser
from bs4 import BeautifulSoup
from ijson import items
from xlwt.Workbook import *

import urllib2
import lxml.html
import re
import time

def get_youtube_ids_from_text(text):
    youtube_ids = []

    if text == None:
        text = ''
    
    # Find all matching youtube links.
    result = re.findall("(https?:\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)(\w*)(&(amp;)?[\w\?=]*)?)", text)
    
    for match in result:
        if match[1] not in youtube_ids:
            youtube_ids.append(match[1])
    
    return youtube_ids 


def get_no_of_views_of_video(browser):
    """ Get no of views of a video opened in browser engine """

    html_response = browser.html
    doc = lxml.html.document_fromstring(html_response)
    
    # Getting the no of views.
    for t in doc.xpath("//div[contains(@class,'watch-view-count')]/text()"):
        return t
    return 0


def get_no_of_likes_dislikes_of_video(browser):
    """ Get no of likes and dislikes of a video """

    html_response = browser.html
    doc = lxml.html.document_fromstring(html_response)

    likes_dislikes = {'likes':0, 'dislikes':0}

    # Getting the no of likes and dislikes.
    for t in doc.xpath("//span[@id='watch-like-dislike-buttons']"):
        
        likes_dislikes['likes'] = t.xpath(".//button[@id='watch-like']/span[contains(@class,'yt-uix-button-content')]/text()")[0]
        likes_dislikes['dislikes'] = t.xpath(".//button[@id='watch-dislike']/span[contains(@class,'yt-uix-button-content')]/text()")[0]    

        return likes_dislikes

    return likes_dislikes


def get_no_of_comments_of_video(browser):
    """ Gets the no of comments of video """

    # Getting the no of comments.
    # For this we need to scroll the page down
    # Then we need to wait until the comments i frame is loaded.
    # When the iframe is loaded then we need to get the details of the no of comments

    browser.execute_script("window.scrollTo(0,document.body.scrollHeight);")
    browser.is_element_present_by_xpath("//iframe[@title='Comment on this']", wait_time=20)
    html_response = browser.html
    soup = BeautifulSoup(unicode(html_response))
    
    # Getting the iframe by title Comment on this.
    for iframe in soup.findAll("iframe", {"title":"Comment on this"}):
        
        # Getting the src attribute of iframe
        # then requesting the content of the iframe.
        try:
            response = urllib2.urlopen(iframe.attrs['src'])
            iframe_soup = BeautifulSoup(response)
            
            for comments in iframe_soup.findAll("div",{"class":"DJa"}):
                return comments.contents[1].strip(" ()")
        except Exception:
            return 0
    return 0


def get_video_details(youtube_video_id):
    """ Gets the details of a video like likes, dislikes, views, comments etc """

    video_details = {}
    
    # Setting the video url
    video_details = {
        'url':"https://www.youtube.com/watch?v=" + youtube_video_id,
        'likes':0,
        'dislikes':0,
        'views':0,
        'comments':0
    }

    try:
        browser = Browser('phantomjs')
        browser.visit("https://www.youtube.com/watch?v=" + youtube_video_id)   
    except Exception:
        return video_details

    video_details['views'] = get_no_of_views_of_video(browser)
    
    likes_dislikes = get_no_of_likes_dislikes_of_video(browser)
    video_details['likes'] = likes_dislikes['likes']
    video_details['dislikes'] = likes_dislikes['dislikes']

    video_details['comments'] = get_no_of_comments_of_video(browser)

    browser.quit()
    return video_details


def get_youtube_ids_from_tweet(tweet_item):
    """ Gets the youtube links from tweet item """

    try:
        total_tweet_text = ""
        total_tweet_text = tweet_item['text']
            
        for media in tweet_item['entities']['media']:
            if "url" in media:
                total_tweet_text = total_tweet_text + " " + media['url']
            
            if "display_url" in media:
                total_tweet_text = total_tweet_text + " " + media['display_url']
            
            if "expanded_url" in media:
                total_tweet_text = total_tweet_text + " " + media['expanded_url']
            
            if "media_url" in media:
                total_tweet_text = total_tweet_text + " " + media['media_url']
            
            if "media_url_https" in media:
                total_tweet_text = total_tweet_text +  " " + media['media_url_https']
        

        for url in tweet_item['entities']['urls']:
            if "url" in url:
                total_tweet_text = total_tweet_text + " " + url['url']
            
            if "expanded_url" in url:
                total_tweet_text = total_tweet_text + " " + url['expanded_url']
            
            if "display_url" in url:
                total_tweet_text = total_tweet_text + " " + url['display_url']
            

        youtube_ids = get_youtube_ids_from_text(total_tweet_text)
        return youtube_ids    
            
    except KeyError:
        youtube_ids = get_youtube_ids_from_text(total_tweet_text)
        return youtube_ids


def callback_sort_video_details(video_details):
    """ This is sort call back function to sort the videos based on count """
    return video_details['count']

def insert_row_to_sheet(ws, row_data, row_no):
    """ Insert row into the work sheet in specific row """
    col_no = 0
    for item in row_data:
        ws.write(row_no, col_no, item)
        col_no = col_no + 1

    return ws

def write_video_details_to_sheet(file_name, videos_details):
    """ Write videos details to the sheet """

    # Initialising the xlwt  workbook.
    wb = Workbook()
    ws = wb.add_sheet('0')

    # convert the videos_details to proper sheet format
    # then write to the sheet

    # Initialising the sheet data
    sheet_data = {"sheet":[]}
    header_data = [
        'video url', 
        'No of views', 
        'No of Likes', 
        'No of dislikes', 
        'No of comments',
        'No of times shared'
    ]
    ws = insert_row_to_sheet(ws, header_data, 0)

    row_no = 1
    for video_details in videos_details:
        video_data = []
        video_data.append(video_details['url'])
        video_data.append(video_details['views'])
        video_data.append(video_details['likes'])
        video_data.append(video_details['dislikes'])
        video_data.append(video_details['comments'])
        video_data.append(video_details['count'])
        
        ws = insert_row_to_sheet(ws, video_data, row_no)
        row_no  = row_no + 1
        
    wb.save(file_name)




def get_print_all_youtubelinks_withdetails():
    """ Get all the you tube links from all the tweets"""

    f = open("sample_tweets_data.json")
    videos_details = {}

    # This list contains the no of times a video occured as key and 
    # for each count it stores the corresponding videos.
    video_count = {}

    youtube_ids = []

    # Iterating through all tweets
    # Then getting all the you tube links
    for item in items(f, "item"):
        
        temp_youtube_ids = get_youtube_ids_from_tweet(item)
        youtube_ids.extend(temp_youtube_ids)

        # Go through the each link and scrap the details
        for video_id in temp_youtube_ids:
            
            # If the video id aldready exists in video_details
            # then get the details of the video.
            # increment the count
            if video_id in videos_details.keys():
                videos_details[video_id]['count'] = videos_details[video_id]['count'] + 1
            else:
                videos_details[video_id] = get_video_details(video_id)
                videos_details[video_id]['count'] = 1

        print "-------video details collected until now by sorted order-----------"
        print sorted(videos_details.values(), key=callback_sort_video_details, reverse=True)
        if len(temp_youtube_ids) != 0:
            write_video_details_to_sheet("videos.xls", sorted(videos_details.values(), key=callback_sort_video_details, reverse=True))

    return videos_details

get_print_all_youtubelinks_withdetails()         
# get_views_likes_dislikes_for_video("UidqhWCyACs")
