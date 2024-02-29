from bs4 import BeautifulSoup
import time
import bs4
import pandas as pd
import requests

BASE_URL = 'http://collegecatalog.uchicago.edu'
columns = ['Department', 'CourseID', 'CourseName', 'Description', 'Instructors', 'TermsOffered','Prerequisites','Equivalent']
link_queue = [BASE_URL]
visited = []
data = []
count = 0
def get_links(soup):
    links = soup.find(class_='nav levelone')
    if not links:
        return
    for link in links.children:
        if not isinstance(link, bs4.NavigableString):
            ref = BASE_URL + link.a.attrs['href']
            if ref not in visited and ref not in link_queue:
                link_queue.append(ref)
    links = soup.find(class_='nav leveltwo')
    if not links:
        return
    for link in links.children:
        if not isinstance(link, bs4.NavigableString):
            ref = BASE_URL + link.a.attrs['href']
            if ref not in visited and ref not in link_queue:
                link_queue.append(ref)
    return

def verify1(soup):
    #if not (soup.find(class_='courseblock main') or soup.find(class_='courseblock sequence')):
    #    return False
    if not soup.find(class_='sc_courseblock'):
        if not soup.find(class_='courses'):
            return False
        return soup.find(class_='courses')
    return soup.find(class_='sc_courseblock')

def verify2(child):
    if not (child.find(class_='courseblocktitle') or child.find(class_='courseblockdesc')):
        return False
    return True

def get_data(urls, count=0):
    if len(urls) == 0:
        return
    ref = urls[-1]
    link_queue.pop(-1)
    visited.append(ref)
    resp = requests.get(ref)
    soup = BeautifulSoup(resp.text, "html.parser")
    get_links(soup)
    if not verify1(soup):
        count += 1
        #print(len(link_queue) ,len(visited))
        time.sleep(3)
        return get_data(link_queue, count)
    main = verify1(soup)
    for child in main.children:
        if not isinstance(child, bs4.NavigableString):
            if not verify2(child):
                continue
            course_name_id = child.find(class_='courseblocktitle').strings
            for string in course_name_id:
                ID1 = string.split('.')[0]
                ID = " ".join(ID1.split('\xa0'))
                dept, cID = ID.split()
                name = string[string.find('.')+1:].strip()
                try:
                    name = name[:name.find('Units') - 4]
                except:
                    pass
            if '-' in string: #Ignores sequences
                continue
            desc = child.find(class_='courseblockdesc').strings
            for string in desc:
                description = string.strip()
            profs = child.find(class_='courseblockdetail').strings
            details = ['N/A', 'N/A', 'N/A', 'N/A']
            strs = []
            for string in profs:
                strs.append(string.strip())
            for string in strs:
                if 'Instructor(s):' in string:
                    details[0] = string[:string.find('Terms')].split(':')[1].strip() #Instructors
                    try:
                        details[1] = string[string.find('Terms'):].split(':')[1].strip() #Terms
                    except:
                        pass
                if 'Prerequisite(s):' in string:
                    details[2] = string.split('(s):')[1].strip() #Prerequisites
                if 'Equivalent Course(s):' in string:
                    details[3] = string.split('(s):')[1].strip() #Equivalent courses
            row = [dept, ID, name, description, details[0], details[1], details[2], details[3]]
            data.append(row)
    time.sleep(3)
    count +=1
    #print(len(link_queue) ,len(visited))
    return get_data(link_queue, count)

get_data(link_queue)
cdf = pd.DataFrame(data, columns=columns)

def clean_terms(col):
    terms = []
    valid_terms = ['Autumn', 'Spring','Winter','Summer']
    for term in valid_terms:
        if term in col:
            terms.append(term)
    if len(terms) == 0:
        return 'None'
    return ", ".join(terms)


cdf['Terms'] = cdf['TermsOffered'].apply(clean_terms)
cdf.to_csv('Course-data.csv')


