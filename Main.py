# define function to get num pages of posts from a subreddit, start collecting at a defined after
#import requests
import praw
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
from pprint import pprint
from praw.models import MoreComments
import re
import requests
import json
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt
from nltk.stem import LancasterStemmer

reddit = praw.Reddit(
client_id="x0xWaHnrnJEXCTv1omiCqA",
client_secret="CvHcn7nyujGBbUysm1oSVAfqDzNyAA",
user_agent="unix:com.example.nflapp:v1.1 (by /u/timpowell21)",
)

# Make sure to add these downloads back to 
# the source code since the instructors 
# will need them in order to run the program
nltk.download('punkt')
nltk.download('words')
nltk.download('vader_lexicon')
nltk.download('stopwords')

stopwords = nltk.corpus.stopwords.words("english")
wordsCorpus = set(nltk.corpus.words.words())

# May want to add using a stemmer too.
# Need to work on removing punctuation.
# Need to add normalization.
# What is the expected outcome and how 
# do I plan on evaluating my work.
# Add graph to look at wins vs. average
# sentiment.
# Look through tutorials I was using to see
# if I could add anything else (another model,
# topic analysis, additional stuff related to 
# main subjects learned from course).
# May want to make same sentiment and correlation
# calculations with data that hasn't been cleaned
# then I can prove that cleaning the data helps.
# May want to add soem more correlations such as
# length of streak. 
# Possibyl try to add some topic modeling with LDA
# if I have time

# Accepts a string, removes special characters,
# removes URLs, tokenizes the string so that we
# can iterate through each word and determine if
# its an english word and it contains letters a-z
# using isalpha(), converts the list of words back
# into a string and returns this string.
def cleanText(text):
    final = "".join(u for u in text if u not in ("(", ")"))
    final = re.sub(r"http\S+", "", final)
    final = "".join(u for u in final if u not in ("?", ".", ";", ":",  "!",'"', ",", "'", "[", "]"))
    final = nltk.word_tokenize(final)
    final = [w for w in final if w.lower() in wordsCorpus and w.isalpha()]
    final = ' '.join(final)
    return final  

# Accepts dict as input. Performs stemming on each 
# value in the dictionary.
def getStemListOfWords(dataDict):
    editedDict = {}
    stemmer = LancasterStemmer()
    for key, value in dataDict.items():
        stemWords = []
        tokens = nltk.word_tokenize(value)
        for word in tokens:
            stem = stemmer.stem(word)
            stemWords.append(stem)
        editedDict[key] = ' '.join(stemWords)
    return editedDict

# Accepts a list of words and uses NLTKs list of 
# stopwords to remove any stop words from the 
# list and returns the words as a string.
def removeStopwords(text):
    textStopWordsRemoved = ""
    for word in text:
        if word.lower() not in stopwords:
            textStopWordsRemoved += str(word + " ")       
    return textStopWordsRemoved

# Accepts a string and returns a frequency distribution.
def getFreqDist(text):
    words: list[str] = nltk.word_tokenize(text)
    fd = nltk.FreqDist(words)
    return fd

# Returns a dictionary of title-comment key-value
# pairs from the specified subreddit. Concatenates 
# the comments for a post into a single string.
def getSubRedditPosts(team):
    titleCommentsDict={}
    for submission in reddit.subreddit(team).hot(limit=1):
        commentString = ""
        print("LOOKING AT NEW POST\n")
        print("The post title is: " + submission.title + "\n")
        # print("Checking comments for this post\n")
        for redditComment in submission.comments:
            if isinstance(redditComment, MoreComments):
                continue
            comment = redditComment.body.lower()
            commentString += " " + str(comment)
        titleCommentsDict[submission.title] = commentString    
    return titleCommentsDict

def getCollectionOfWords(dataDict):
    collection = ""
    for key, value in dataDict.items():
        collection += value
    return collection
        
# Accepts a dictionary of title-comment key-value 
# pairs and cleans the comment values. Returns a new
# dictionary with the updated comments. 
def cleanSubRedditPosts(data):
    editedDict = {}
    for key in data:
        #print("This is the comment prior to cleaning: " + str(data[key]) + "\n")
        comment = data[key].lower()
        commentCleaned = cleanText(comment)
        listOfWords = commentCleaned.split()
        commentStopwordsRemoved = removeStopwords(listOfWords)
        #print("This is the comment after cleaning: " + str(commentStopwordsRemoved) + "\n")
        editedDict[key] = commentStopwordsRemoved
    return editedDict
        
        
# Receives dict of title-comment key-value pairs. Calculates 
# the polarity scores for each post. Returns the average compound score.
# Vader needs raw strings for its ratings, not word lists. 
# Returns average compound score for all comments. This is 
# using NLTKs pre-trained sentiment analyzer.       
def sentimentAnalyzer(data):
    sia = SIA()
    results = []
    compound = 0
    
    for key in data:
        scores = sia.polarity_scores(data[key])
        scores['title'] = key
        scores['comments'] = data[key]
        results.append(scores)
        compound += scores["compound"]    

    return compound/len(data)

# Parse given json file. For each team in the 
# teamNames list, we want to find this team in 
# the json file and determine how many wins they
# have and what the result of their last game was. 
def parseJson(jsonfile, teamNames):
    
    winsDict = {}
    
    with open(jsonfile) as f:
        data = json.load(f)
    
    conferences = data["conferences"]
    for conference in conferences:   
        divisions = conference["divisions"]
        for division in divisions:
            teams = division["teams"]
            for team in teams:
                name = team["name"]
                if name in teamNames:
                    wins = team["wins"]
                    streak = team["streak"]
                    streakType = streak["type"]
                    pointsFor = team["points_for"]
                    winsDict[name] = {}
                    winsDict[name]["Team"] = name
                    winsDict[name]["Wins"] = wins
                    winsDict[name]["Points For"] = pointsFor
                    if streakType == "win":
                        winsDict[name]["Streak"] = True
                    else:
                        winsDict[name]["Streak"] = False
    return winsDict
     

# Fetch the nfl data json using the sportradar api.
# API key removed from function for security. Json file
# stored at data/nfl.json.
def getJson():
    response = requests.get("https://api.sportradar.us/nfl/official/trial/v7/en/seasons/2021/REG/standings/season.json?api_key=mdqex7r4gdjvgj574cnmsatv")
    with open('data/nfl.json', 'wb') as f:
        f.write(response.content)
        return f

# Calculate the correlation between each team's 
# wins and public sentiment. Calculate the 
# correlation between each team's most recent 
# outcome and public sentiment.    
def calculateCorrelation(dataDict):
    wins = []
    averageSentiments = []
    streak = []
    pointsFor = []
    for team in dataDict:
        teamDict = dataDict[team]
        wins.append(teamDict["Wins"])
        averageSentiments.append(teamDict["Average Sentiment Score"])
        streak.append(teamDict["Streak"])
        pointsFor.append(teamDict["Points For"])
    print("This application uses the Pearson Correlation Coefficient to compare the correlation between (team's win total vs. public sentiment) and (team's most recent outcome vs. public sentiment)." + "\n")
    print("The range for the Pearson Correlation Coefficient is [-1,1]. A -1 means there is a strong negative correlation while a 1 means there is a strong positive correlation." + "\n")
    print("Pearson Correlation Coefficient Results:" + "\n")
    r, p = scipy.stats.pearsonr(wins, averageSentiments)
    print("The Pearson Correlation Coefficient between wins and public sentiment is: \n" + str(r) + "\n")
    r, p = scipy.stats.pearsonr(streak, averageSentiments)
    print("The Pearson Correlation Coefficient between most recent outcome and public sentiment is: \n" + str(r) + "\n")
    r, p = scipy.stats.pearsonr(pointsFor, averageSentiments)
    print("The Pearson Correlation Coefficient between points for and public sentiment is: \n" + str(r) + "\n")

# Plot the wins and average sentiments in a
# scatter plot. 
def plotData(dataDict):
    wins = []
    averageSentiments = []
    for team in dataDict:
        teamDict = dataDict[team]
        wins.append(teamDict["Wins"])
        averageSentiments.append(teamDict["Average Sentiment Score"])
    plt.scatter(wins, averageSentiments, alpha=0.5)
    plt.show() 

# Predict the result of the next game based off
# the average public sentiment.     
def getGamePrediction(averageSentiment):
    if averageSentiment > 0.3:
        return "Win"
    else:
        return "Loss"

# Determine which team had the highest public sentiment.    
def getMostFavoredTeam(dataDict):
    highestSentiment = 0
    highestSentimentTeam = ""
    for team in dataDict:
        teamDict = dataDict[team]
        sentiment = teamDict["Average Sentiment Score"]
        if sentiment > highestSentiment:
            highestSentiment = sentiment
            highestSentimentTeam = teamDict["Team"] 
    print("The team with the highest public sentiment is the " + highestSentimentTeam + "\n")

# Determine which team had the lowest public sentiment.    
def getLeastFavoredTeam(dataDict):
    lowestSentiment = 0
    lowestSentimentTeam = ""
    for team in dataDict:
        teamDict = dataDict[team]
        sentiment = teamDict["Average Sentiment Score"]
        if sentiment < lowestSentiment:
            lowestSentiment = sentiment
            lowestSentimentTeam = teamDict["Team"] 
    print("The team with the lowest public sentiment is the " + lowestSentimentTeam + "\n")
        
       
    
def main():
    teamNames = ["Patriots", "Giants", "Jaguars", "Jets", "Titans", "Ravens", 
                "Lions", "Bears", "Steelers", "Bills", "Dolphins"]
    subreddits = ["patriots", "nygiants", "jaguars", "nyjets", "Tennesseetitans", 
                 "ravens", "detroitlions", "chicagobears", "steelers", "buffalobills", "miamidolphins"]
    
    # After retrieving the json, this doesn't need to be
    # called again. If we call it every time the program is
    # run, then I'll run out of API calls. Only call when the
    # statistics are outdated (another game has occured).
    # xml = getJson()

    teamDict = parseJson('data/nfl.json', teamNames)
    
    # For each team in the list created above, we're going
    # to retrieve the posts/post comments from this teams
    # subreddit, combine all of the text data, clean the text data,
    # calculate the sentiment for this teams text data, and add it 
    # to the dictionary of team data.
    for i in range(len(teamNames)):
        print("Retrieving data and calculating average sentiment for " + str(teamNames[i]) + "\n")
        reddit.read_only = True
        data = getSubRedditPosts(subreddits[i])
        editedData = cleanSubRedditPosts(data)
        averageCompound = sentimentAnalyzer(editedData)
        collection = getCollectionOfWords(editedData)
        freqDist = getFreqDist(collection)
        print("The average sentiment score for the " + str(teamNames[i]) + 
              " is: " + str(averageCompound) + "\n")
        teamDict[teamNames[i]]["Average Sentiment Score"] = averageCompound
        teamDict[teamNames[i]]["Most Common Words"] = freqDist.most_common(5) 
        teamDict[teamNames[i]]["Predicted Result of Next Game"] = getGamePrediction(averageCompound)
    pprint(teamDict)
    print("\n")
    calculateCorrelation(teamDict)
    getMostFavoredTeam(teamDict)
    getLeastFavoredTeam(teamDict)
        
if __name__ == '__main__':
    main()