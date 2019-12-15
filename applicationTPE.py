import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tweepy
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
from matplotlib import style
import threading
import time
import os
from textblob import TextBlob
import pandas as pd
import numpy as np
# identifiants à récupérer dans les paramètres twitter de votre compte
consumer_key = "epeiJTdxomeEnsQQp5lq3h5O4"
consumer_secret = "IvxExjRu0jplUvyoW0fc4w4G3177kztDaFXomg40WWMn7pKz1n"
access_token = "1179225305212305408-5X1wLUCu7qc6xeO9MzbquSfWYWuWvx"
access_token_secret = "ONnUkLFGtQgg4TUUH0fV1SMY6DYEsJLQdHciqwHHCwVxi"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
xar = list()
yar = list()
should_stop = False
unite_temps = 5 # 5 secondes pour l'agrégation des données
nbr_points = 30 # 30 points sur le graphique
dataframe_tweets = pd.DataFrame(columns=['timestamp_ms', 'keyword_id',
                      'polarity', 'subjectivity'])
print(dataframe_tweets)
# INTERFACE
app = tk.Tk()
app.wm_title("Stockagecen mongodb et visualisation de donnees ")
style.use("ggplot")
fig = Figure(figsize=(8, 5), dpi=112)
ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212, sharex=ax1)
ax2.set_xlabel('Temps')
ax1.set_ylabel('Keyword 1', color='g')
ax2.set_ylabel('Leyword 2', color='r')
fig.set_tight_layout(True)
# Groupbox de visualisation
groupbox_visualisation = tk.LabelFrame(
    master=app, text="Visualisation", padx=5, pady=5)
groupbox_visualisation.pack(fill='both',
                            expand=True, padx=10, pady=10, side="left")
graph = FigureCanvasTkAgg(fig, master=groupbox_visualisation)
canvas = graph.get_tk_widget()
canvas.pack(side="top", fill='both', expand=True)
# Groupbox de paramètres
groupbox_param = tk.LabelFrame(
    master=app, text="Paramètres", padx=5, pady=5)
groupbox_param.pack(fill='both',
                    expand=True, padx=10, pady=10, side="right")
groupbox_param.grid_columnconfigure(1, weight=1)
# Premier mot clé
label_widget_1 = tk.Label(groupbox_param, text="Mot-clé à chercher (1) : ")
label_widget_1.grid(row=0, sticky="w")
premier_keyword = tk.Entry(master=groupbox_param)
premier_keyword.grid(row=0, column=1, sticky="ew")
premier_keyword.insert(0, "ebola")
# Deuxième mot clé
label_widget_2 = tk.Label(
    groupbox_param, text="Mot-clé à chercher (2): ")
label_widget_2.grid(row=1, sticky="w")
deuxieme_keyword = tk.Entry(master=groupbox_param)
deuxieme_keyword.grid(row=1, column=1, sticky="ew")
deuxieme_keyword.insert(0, "pollution")
def lancer_analyse():
    """ Fonction appelée lors du clic sur le bouton d'analyse """
    global should_stop, listening_twitter_thread
    should_stop = True  # permet d'arreter l'analyse des anciens mots-clés
    listening_twitter_thread.join() # dès que l'ancien thread se termine
    # relance une analyse avec les nouveaux mots-clés
    listening_twitter_thread = threading.Thread(
        target=start_listening_twitter)
    listening_twitter_thread.start()
def fermer_programme():
    global should_stop
    if tk.messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter ?"):
        # Normalement on doit cloturer plus proprement le thread principal
        # et le thread secondaire. 0 pour indiquer au système que tout a fonctionné.
        os._exit(0) 
app.protocol("WM_DELETE_WINDOW", fermer_programme)
# Bouton d'analyse
bouton_analyse = tk.Button(master=groupbox_param,
                           text="Lancer l'analyse !", command=lancer_analyse)
bouton_analyse.grid(row=2, column=0, columnspan=2)
# Liste des tweets avec scrollbar
liste_tweets = ttk.Treeview(master=groupbox_param)
liste_tweets["columns"] = ("tweet", "timestamp", "polarity", "subjectivity")
liste_tweets.column("tweet", width=220)
liste_tweets.column("timestamp", width=50)
liste_tweets.column("polarity", width=20)
liste_tweets.column("subjectivity", width=20)
liste_tweets.heading("tweet", text="Tweet")
liste_tweets.heading("timestamp", text="Timestamp")
liste_tweets.heading("polarity", text="Polarité")
liste_tweets.heading("subjectivity", text="Subjectivité")
liste_tweets.grid(row=3, column=0, columnspan=2, sticky="nsew")
    
# Bouton quitter
bouton_quitter = tk.Button(master=groupbox_param,
                           text="Quitter le programme", command=fermer_programme)
bouton_quitter.grid(row=4, column=0, columnspan=2, sticky="s")
# FONCTIONS
def get_back_values():
    # On supprime les trop vielles valeurs
    global dataframe_tweets
    print(dataframe_tweets)
    dataframe_tweets.index = pd.to_datetime(dataframe_tweets.timestamp_ms, unit="ms")
    dataframe_tweets = dataframe_tweets.drop(
        dataframe_tweets[dataframe_tweets.timestamp_ms.astype(int) < int(round(time.time() * 1000)) - unite_temps * nbr_points * 1000].index)
    x = range(nbr_points)
    try:
        y1 = dataframe_tweets[dataframe_tweets.keyword_id ==
                          True].polarity.resample(str(unite_temps) + 'S').mean().fillna(method='backfill')
        y2 = dataframe_tweets[dataframe_tweets.keyword_id ==
                          False].polarity.resample(str(unite_temps) + 'S').mean().fillna(method='backfill')
    except:
        return get_back_values()
   
    # Si la longueur du tableau est insuffisante (vrai à l'initialisation), on remplit avec des 0
    y1 = np.pad(y1, max(nbr_points - len(y1), 0), 'constant', constant_values=(0))[-nbr_points:]
    y2 = np.pad(y2, max(nbr_points - len(y2), 0), 'constant', constant_values=(0))[-nbr_points:]
    
    return x, y1, y2
 
def update_graph(dt):
    x, y1, y2 = get_back_values()
    ax1.clear()
    ax2.clear()
    ax1.set_ylim(-1, 1, auto=False)
    ax2.set_ylim(-1, 1, auto=False)
    ax2.set_xlabel('Temps')
    ax1.set_ylabel(premier_keyword.get(), color='g')
    ax2.set_ylabel(deuxieme_keyword.get(), color='r')
    ax1.plot(x, y1, 'g-o')
    ax2.plot(x, y2, 'r-o')
def convertir_str(chaine):
    char_list = [chaine[j]
                 for j in range(len(chaine)) if ord(chaine[j]) in range(65536)]
    resultat = ''
    for j in char_list:
        resultat = resultat + j
    return resultat
class TwitterListener(tweepy.StreamListener):
    def on_status(self, status):
        global should_stop, dataframe_tweets
        if should_stop:
            should_stop = False
            return False
        if len(xar) == 0:
            xar.append(0)
        else:
            xar.append(xar[-1] + 1)
        yar.append(int(status.user.id_str))
        texte_tweet = convertir_str(status.text)
        tweet_analysis = TextBlob(texte_tweet)
        # Ajout à la liste des tweets
        liste_tweets.insert("", "end",    text=status.id, values=(
            str(texte_tweet),
            str(status.timestamp_ms),
            tweet_analysis.polarity,
            tweet_analysis.subjectivity))
        is_first_keyword = premier_keyword.get().casefold() in map(str.casefold, texte_tweet.split())
        dataframe_tweets = dataframe_tweets.append({
            "timestamp_ms": int(status.timestamp_ms),
            "keyword_id": is_first_keyword,
            "polarity": tweet_analysis.polarity,
            "subjectivity": tweet_analysis.subjectivity
        }, ignore_index=True)
        # 50 derniers tweets affichés
        if len(liste_tweets.get_children()) > 50:
            premier_item = liste_tweets.get_children()[0]
            liste_tweets.delete(premier_item)
            # On défile vers le dernier élément
            liste_tweets.see(liste_tweets.get_children()[-1])
def start_listening_twitter():
    myStreamListener = TwitterListener()
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
    myStream.filter(track=[premier_keyword.get(), deuxieme_keyword.get()])
listening_twitter_thread = threading.Thread(
    target=start_listening_twitter)
listening_twitter_thread.start()
# Callback de rafraichissement du graphique toutes les 500ms
ani = animation.FuncAnimation(fig, update_graph, interval=500)
# Boucle d'événement principal, lance la fenetre, gere les interactions
app.mainloop()

