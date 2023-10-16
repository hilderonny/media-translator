# media-translator

Mit diesem Tool kann man Audio- und Videodateien transkribieren und den Text ins Deutsche übersetzen.

## Einrichtung der Entwicklungsumgebung

Zuerst muss Python mit der Version 3.11.6 (neuere Versionen haben ein Problem mit der Installation von faster-whisper) mit der Erweiterung "TCL/TK" installiert werden. https://www.python.org/downloads/windows/

![](images/python-installer-1.png)
![](images/python-installer-2.png)

Die grafische Oberfläche benutzt [PySimpleGUI](https://www.pysimplegui.org/) und wir per `pip` installiert.

```
pip install pysimplegui
```

Die Transkription und Übersetzung ins Englische erfolgt über [Faster Whisper](https://github.com/guillaumekln/faster-whisper).

```
pip install faster-whisper
```

Für die Übersetzung von Englisch nach Deutsch wird [Argos Translate](https://github.com/argosopentech/argos-translate) benutzt.

```
pip install argostranslate
```

Das Kompilieren in eine ausführbare EXE-Datei erfolgt mit [PyInstaller](https://pyinstaller.org/en/stable/).

```
pip install pyinstaller
```

## EXE-Datei kompilieren

Das Programm kann auch ohne vorhandene KI-Modelle kompiliert werden.

```
pyinstaller -w MediaTranslator.pyw
```

Dabei wird ein Verzeichnis `dist/MediaTranslator` erstellt, in dem die EXE-Datei abgelegt wird. Diese Datei ist dann portabel ausführbar, sofern alle anderen Dateien und Unterverzeichnisse vorhanden sind.

In dieses Verzeichnis muss auch das `data` Verzeichnis mit den KI-Modellen kopiert werden, also nach `dist/data`.

## KI Modelle herunterladen

Die KI-Modelle für Faster Whisper müssen sich im Unterverzeichnis `./data/faster-whisper` befinden, die für Argos Translate in `./data/argos-translate`.

Faster Whisper lädt automatisch fehelnde Modelle herunter, sobald das Programm ausgeführt wird und auf das entsprechende Modell zugreifen möchte.

Für Argos Translate müssen die Modelle vorab geladen werden:

```
python ./download_argos_models.py
```
