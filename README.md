Frissítés:
Mostantól visszanézhetők a magyar műsorok, amik felkerültek a mediaklikk-re. Igény szerínt bővíthető a lista.

# 📺 Magyar TV (MTVA) IPTV Generátor

Mivel nem találtam jelenleg jól működő megoldást a magyar adók házi streamelésére, készítettem egy kis scriptet, amit Jellyfin média szerverbe könnyedén lehet integrálni.

Ez a projekt egy pehelysúlyú, dockerizált python alkalmazás, ami egy folyamatosan frissülő, élő M3U lejátszási listát generál a magyar állami televíziócsatornákhoz. 

A hivatalos MTVA streamek biztonsági tokeneket használnak, amik percek alatt lejárnak. Ez a kód megkerüli a lejáró linkek problémáját, így a csatornák stabilan és megszakítás nélkül nézhetők bármilyen IPTV lejátszóban vagy médiaszerverben (Jellyfin, Emby, Plex, VLC).

## 📺 Támogatott Csatornák
* M1 HD
* M2 HD
* M4 Sport HD
* M4 Sport+ HD
* M5 HD
* Duna HD
* Duna World HD


## 🚀 Telepítés (Docker)

A telepítéshez Docker és Docker Compose szükséges.

1. Klónozd a tárolót:
```
   git clone https://github.com/penguinpit/magyartv.git
```
```
   cd magyartv
```
2.
  ```
   docker compose up -d --build
  ```
A generátor mostantól a háttérben fut.
Az M3U lejátszási listádat a következő linken éred el:
```
   http://<A_SZERVERED_IP_CIME>:8000/m3u
```
## 🚀 Jellyfin integráció

. A Tuner hozzáadása
Lépj a Jellyfin Vezérlőpult -> Élő TV menüjébe.

Kattints a Tuner eszközök alatt a + gombra.

Típus: M3U Tuner.

Fájl vagy webcím:
```
http://<A_SZERVERED_IP_CIME>:8000/m3u
```
```
Mentés, és műsorujság frissítése gombra katt
```
## 👉Egyéb megjegyzések👈
A legtöbb beállítás hagyható defaulton, viszont a fMP4 átkódoló konténer engedélyezése résznél érdemes kivenni a pipát, ha bent volt, ellenkező esetben a terhelés jelentősen megugrik. A többi maradhat.
Böngészős lejátszás nem javasolt, mivel a böngészők sajátossága miatt gond lehet a hang lejátszásával. Javasolt Android TV vagy Desktop alkalmazás használata a lejátszáshoz.
Műsorújság egyelőre még nincs beépítve.
Vállalkozó szelleműek kiegészíthetik ezt a kis projektet ezzel a funkcióval.

<img width="1091" height="793" alt="image" src="https://github.com/user-attachments/assets/29eb5983-38dc-4947-a9aa-8a04d52b1647" />
