# PDF vers PPT

Convertit un PDF en PowerPoint (.pptx) **sans rien changer au contenu** : chaque page est
rendue en image en qualité maximale (600 dpi, PNG sans perte) et posée plein cadre sur une diapositive.
Le résultat n'est pas éditable, exactement comme si on glissait une image par page.
La taille de diapositive suit le format du PDF (A4, 16:9, etc.). Compatible PowerPoint Mac et PC, Keynote, LibreOffice.

## Utilisation
Glissez un ou plusieurs PDF dans la fenêtre (ou cliquez pour choisir).
Sous Mac, vous pouvez aussi glisser le PDF sur l'icône de l'app dans le Dock ; sous Windows, sur le .exe.
Aucune option : toujours la qualité maximale (600 dpi, images PNG sans perte).
Le PowerPoint est enregistré à côté du PDF, avec le même nom (jamais d'écrasement : « nom (2).pptx »).

## Construire les applications
- **Mac M1** : `bash build_mac.sh` → `dist/PDF vers PPT.app`
- **Windows 10/11** : double-cliquer `build_windows.bat` sur un PC Windows → `dist\PDF vers PPT.exe`
- **Les deux automatiquement** : pousser ce dossier sur GitHub ; l'onglet Actions → « Build PDF vers PPT » → *Run workflow*
  produit le .zip Mac et le .exe Windows à télécharger.

## Premier lancement
- Mac : si macOS bloque l'app (téléchargée), clic droit → Ouvrir, ou `xattr -cr "PDF vers PPT.app"`.
- Windows : SmartScreen peut afficher « Windows a protégé votre ordinateur » → *Informations complémentaires* → *Exécuter quand même*
  (l'exe n'est pas signé avec un certificat payant).
