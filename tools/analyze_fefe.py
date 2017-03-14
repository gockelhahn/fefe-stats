#!/usr/bin/env python3

# Hint: just use ipython and stay active for working with DataFrame "df"

import os
import re
import bleach
import datetime as dt
from io import StringIO
from lxml import html
from urllib.parse import urlparse
import collections
from operator import itemgetter
import pandas as pd
import matplotlib.pyplot as plt

post_directory = 'post'
posts = []

if not os.path.exists(post_directory):
    print('Directory "' + post_directory + '" not found. Exit.')
    os.sys.exit(1)

# find features in posts
for post in os.listdir('post'):
    # assemble file name
    filename = os.path.join(post_directory, post)
    # get last modified date (creation time)
    created = dt.datetime.fromtimestamp(os.path.getmtime(filename))
    # read posts content
    filecontent = ''
    with open(filename, 'r') as f:
        filecontent = f.read()
    # remove newlines
    filecontent = filecontent.replace('\n', '')
    # only give posts text instead header/footer
    filecontent = filecontent.split('[l]</a>')[1]
    filecontent = filecontent.split('</ul><p><div')[0]
    # get text only by removing all html tags
    text = bleach.clean(filecontent, tags=[], attributes={}, styles=[], strip=True)
    text = text.strip()
    # count updates
    updates = filecontent.count('<b>Update')
    # count quotes
    quotes = filecontent.count('</blockquote>')
    quotes += filecontent.count('</pre>')
    quotes += filecontent.count('</q>')
    # count tables
    tables = filecontent.count('</table>')
    # get html structure for using xpath
    try:
        tree = html.parse(StringIO(filecontent))
    except:
        # needed in some python versions
        tree = html.parse(StringIO(filecontent.decode('utf-8')))
    # get all links in blog post
    links = tree.xpath('//a/@href')
    # get all images
    images = tree.xpath('//img/@src')
    # get all videos
    videos = tree.xpath('//object/embed/@src')
    videos += tree.xpath('//video/source/@src')
    # get all audios
    audios = tree.xpath('//audio/source/@src')
    # add blog post to list
    posts.append({'name': post, 'created': created, 'text': text, 'updates': updates, 'quotes': quotes, 'tables': tables, 'links': links,'images': images, 'videos': videos, 'audios': audios})


# check if given link is linking to fefes blog itself
def is_internal_link(link):
    url = urlparse(link)
    if url.netloc.lower() == 'blog.fefe.de' or (url.netloc == '' and (url.path == '' or url.path == '/')):
        return True
    return False


# check if internal post is referenced
def is_internal_reference(link):
    if is_internal_link(link):
        tmp = link.split('ts=')
        if len(tmp) > 1:
            return True
    return False


# get internal link name
def get_link_name(link):
    tmp = link.split('ts=')
    if len(tmp) > 1:
        # cut off further parameters
        return tmp[-1].split('&')[0]


# count internal link chain
def count_chain(post, depth=0, hist=[]):
     maxdepth = depth
     links = df[df['name'] == post]['links']
     if len(links) > 0:
        for link in links[0]:
            if is_internal_reference(link):
                newlink = get_link_name(link)
                if newlink not in hist:
                    newlinkdepth = count_chain(newlink, depth + 1, hist + [ post ])
                    if newlinkdepth > maxdepth:
                        maxdepth = newlinkdepth
                #else:
                    ## show circular references
                    #print(post + ' ' + str(hist) + ' ' + newlink)
     return maxdepth


def count_internal_links(links):
    counter = 0
    for link in links:
        if is_internal_link(link):
            counter += 1
    return counter


def count_internal_reference(links):
    counter = 0
    for link in links:
        if is_internal_reference(link):
            counter += 1
    return counter


def count_external_links(links):
    counter = 0
    for link in links:
        if not is_internal_link(link):
            counter += 1
    return counter


# check if given link is using prot
# if explicit==False, assume links like
# '//www.heise.de' as the same protocol as prot
def is_prot(link, prot, explicit=True):
    url = urlparse(link)
    if not explicit:
        if url.scheme == '':
            return True
    if url.scheme == prot:
        return True
    return False


# check if given link is not http/https/[empty]
def is_prot_non_web(link):
    url = urlparse(link)
    if url.scheme != '' and url.scheme != 'http' and url.scheme != 'https':
        return True
    return False


def count_non_web(links):
    counter = 0
    for link in links:
        if is_prot_non_web(link):
            counter += 1
    return counter


# count given links when prot matches
# if only_external==True, count only external links
def count_prot(links, prot, only_external=False):
    counter = 0
    for link in links:
        if only_external:
            if is_internal_link(link):
                continue
        if is_prot(link, prot):
            counter += 1
    return counter


# count given links when domain matches
# if fixwww==True, add missing "www" to domain
def count_domain(links, domain, fixwww=True):
    if fixwww:
        # if domain has no subdomain, add www
        if domain.count('.') == 1:
            domain = 'www.' + domain
    counter = 0
    for link in links:
        url = urlparse(link)
        netloc = url.netloc
        if fixwww:
            # if url has no subdomain, add www
            if netloc.count('.') == 1:
                netloc = 'www.' + netloc
        if netloc.lower() == domain.lower():
            counter += 1
    return counter


# count given substring in text
# if ignorecase==True, ignore the case
def count_in_text(text, substring, ignorecase=True):
    # match chained words characters to find words
    pattern = re.compile("[\w]+")
    # add spaces in front the first words, between words and after  last word
    text = ' ' + ' '.join(pattern.findall(text)) + ' '
    # add spaces in front and after the string to be searched
    substring = ' ' + substring + ' '
    if ignorecase:
        text = text.lower()
        substring = substring.lower()
    counter = 0
    start = 0
    while True:
        # find = -1 if string was not found
        start = text.find(substring, start) + 1
        if start > 0:
            counter += 1
        else:
            return counter


# for df.groupby -> accumulate all lists entries in given list
def sum_list_length(series):
    counter = 0
    for i in series:
        counter += len(i)
    return counter


# import list into pandas
df = pd.DataFrame(posts)
# set "created" column as index
df = df.set_index(pd.DatetimeIndex(df['created'], inplace=True))
# sort by index/time
df.sort_index(inplace=True)

# statistics
# get sum of posts/updates/quotes/links/textlenth
c_posts = df.created.count()
c_updates = df.updates.sum()
c_quotes = df.quotes.sum()
c_links = sum([len(x) for x in df.links])
c_textlength = df.text.str.len().sum()
# get stats per day
dftmp = df.groupby(pd.TimeGrouper(freq='1D', closed = 'left')).created.count()
# amount of all days between first posts and last post
c_days = len([x for x in dftmp])
# get max posts per day
d_posts = dftmp[dftmp.argmax]
# get max updates per day
dftmp = df.groupby(pd.TimeGrouper(freq='1D', closed = 'left')).updates.sum()
d_updates = dftmp[dftmp.argmax]
# get max quotes per day
dftmp = df.groupby(pd.TimeGrouper(freq='1D', closed = 'left')).quotes.sum()
d_quotes = dftmp[dftmp.argmax]
# get max links per day
dftmp = df.groupby(pd.TimeGrouper(freq='1D', closed = 'left')).links.apply(sum_list_length)
d_links = dftmp[dftmp.argmax]
# get max text per day
dftmp = df.groupby(pd.TimeGrouper(freq='1D', closed = 'left')).text.apply(sum_list_length)
d_text = dftmp[dftmp.argmax]
# get stats per post
p_updates = df.updates[df.updates.argmax]
p_quotes = df.quotes[df.quotes.argmax]
p_links = len(df.links[df.links.apply(len).argmax])
p_text = len(df.text[df.text.apply(len).argmax])
# print stats
print('Posts: ' + str(c_posts) + ' / pro Tag (ø): ' + str(round(c_posts/c_days, 2)) + ' / pro Post (ø): ' + str('-') + ' / pro Tag (max): ' + str(d_posts) + ' / pro Post (max): ' + str('-'))
print('Updates: ' + str(c_updates) + ' / pro Tag (ø): ' + str(round(c_updates/c_days, 2)) + ' / pro Post (ø): ' + str(round(c_updates/c_posts, 2)) + ' / pro Tag (max): ' + str(d_updates) + ' / pro Post (max): ' + str(p_updates))
print('Zitate: ' + str(c_quotes) + ' / pro Tag (ø): ' + str(round(c_quotes/c_days, 2)) + ' / pro Post (ø): ' + str(round(c_quotes/c_posts, 2)) + ' / pro Tag (max): ' + str(d_quotes) + ' / pro Post (max): ' + str(p_quotes))
print('Links: ' + str(c_links) + ' / pro Tag (ø): ' + str(round(c_links/c_days, 2)) + ' / pro Post (ø): ' + str(round(c_links/c_posts, 2)) + ' / pro Tag (max): ' + str(d_links) + ' / pro Post (max): ' + str(p_links))
print('Textlänge: ' + str(c_textlength) + ' / pro Tag (ø): ' + str(round(c_textlength/c_days, 2)) + ' / pro Post (ø): ' + str(round(c_textlength/c_posts, 2)) + ' / pro Tag (max): ' + str(d_text) + ' / pro Post (max): ' + str(p_text))

# posts without links/media/quotes
blank_posts = len(df[df.images.apply(len) == 0][df.videos.apply(len) == 0][df.quotes == 0][df.links.apply(len) == 0])
print('Posts ohne Links/Medien/Zitate: ' + str(blank_posts))

# make chart of posting day times
# accumulate amount of postings every 30 minutes
dftmp = df.groupby(pd.TimeGrouper(freq='30Min', closed = 'left')).created.count()
# create a with all dates from above
times = pd.DatetimeIndex(dftmp.index)
# and then group all entries into those slots
dfplot = dftmp.groupby([x.strftime('%H:%M') for x in times.time]).sum()
# show plot
plot = dfplot.plot(kind='bar', figsize=(10,6))
plot.set_ylabel('Anzahl der Blogposts')
plot.patches[25].set_facecolor('#aa3333')
plt.savefig('fefe_uhrzeit.png', bbox_inches='tight')
plt.close()

# make chart of posting day times
# eliminate fake times before 01.07.2005
dftmp = df[df['created'] > '2005-07-01 13:00:00']
# accumulate amount of postings every 30 minutes
dftmp = dftmp.groupby(pd.TimeGrouper(freq='30Min', closed = 'left')).created.count()
# create a with all dates from above
times = pd.DatetimeIndex(dftmp.index)
# and then group all entries into those slots
dfplot = dftmp.groupby([x.strftime('%H:%M') for x in times.time]).sum()
# show plot
plot = dfplot.plot(kind='bar', figsize=(10,6))
plot.set_ylabel('Anzahl der Blogposts')
plt.savefig('fefe_uhrzeit_fixed.png', bbox_inches='tight')
plt.close()

# make chart domains occurences
#dftmp = df
#dftmp = dftmp.drop(['tables', 'updates', 'quotes'], axis=1)
#dftmp['www.twitter.com'] = df.links.apply(count_domain, args=('www.twitter.com',))


# count word occurences
words = []
pattern = re.compile("[\w]+")
for post in posts:
    temp = pattern.findall(post['text'])
    for i in temp:
        # min 2 characters + first letter is capital
        if len(i) >= 2 and i[0].isupper():
            words.append(i)
word_occurence = collections.Counter(words)
word_sorted_occurence = sorted(word_occurence.items(), key=itemgetter(1), reverse=True)
with open('words.txt', 'w') as f:
    f.write('\n'.join(words))
#wordcloud_cli.py --text words.txt --stopwords stopwords --width 1000 --height 600 --imagefile fefe_word_cloud.png


# domains occurences
domains = []
for post in posts:
    for link in post['links']:
        # parse links to find domain
        link = urlparse(link)
        domain = link.netloc
        # if domain has no subdomain, add www
        if domain.count('.') == 1:
            domain = 'www.' + domain
        domains.append(domain)
domain_occurence = collections.Counter(domains)
domain_sorted_occurence = sorted(domain_occurence.items(), key=itemgetter(1), reverse=True)
with open('domains.txt', 'w') as f:
    f.write('\n'.join(domains))


# filetype occurences
filetypes = []
for post in posts:
    for link in post['links']:
        url = urlparse(link)
        # split string at dot (file extention)
        urlsplit = url.path.lower().split('.')
        # if at least one dot
        if len(urlsplit) > 1:
            # if last chunk is less than 8 characters, add to list
            if len(urlsplit[-1]) < 8:
                filetypes.append(urlsplit[-1])
filetype_occurence = collections.Counter(filetypes)
filetype_sorted_occurence = sorted(filetype_occurence.items(), key=itemgetter(1), reverse=True)
with open('filetypes.txt', 'w') as f:
    f.write('\n'.join(filetypes))

