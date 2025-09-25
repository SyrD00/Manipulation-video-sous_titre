## **Connaitre la liste de mes commits(historique des modifications)**
	git log --oneline

exemple:

fe19e07 (HEAD -> main, origin/main, origin/HEAD) restauration dossier capcut
ae99735 update read me mfa aligner
387f407 update
095d181 update Captions and aligner
e4481a8 change arborescence subtitle
3018d15 update generate faster whisper
5297b94 update traduction_sub et whisper


tu veux recuperer tout ce que tu avais fait avant de push(update read me mfa aligner),alors le hashcode sera **e4481a8**

## **Créer une branche temporaire avec l'etat du dossier que tu veux restaurer**

git checkout -b recup-dossier_suppr  e4481a8

la nouvelle branche se nommera **recup-dossier_suppr**

Une fois que t'as recupere ce qui t'intéressait tu peux :

## **Supprimer la branche**

git branch -d recup-dossier_suppr

Mais ava,nt de lancer cette commande,faut changer de branche,tu peux pas supprimer **recup-dossier_suppr** si t'es actuellemnt dans cette branche
