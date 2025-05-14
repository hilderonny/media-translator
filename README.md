# media-translator

## Entwicklung

Unter Windows 10/11 zuerst [Python 3.13.3](https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe) installieren.
Dabei Standard-Installation mit Admin Rechten und PATH-Angabe auswählen.
Dann in das Repository-Verzeichnis wechseln und Kommandozeile öffnen.

https://github.com/Purfview/whisper-standalone-win/releases/tag/libs

Zu https://github.com/spyoungtech/FreeSimpleGUI gewechselt, weil PySimpleGUI closed source wurde.

Um Sentencepiece mit Pathon 3.13 zum Laufen zu bringen, braucht man https://pypi.org/project/dbowring-sentencepiece/.

```cmd
python -m venv venv
venv\Scripts\activate
pip install faster-whisper==1.1.1
pip install FreeSimpleGUI==5.2.0
pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu118
pip install transformers==4.51.3
pip install langdetect==1.0.9
pip install dbowring-sentencepiece==0.2.1
```

https://github.com/Purfview/whisper-standalone-win/releases/download/libs/cuBLAS.and.cuDNN_CUDA12_win_v3.7z

Die Dateien aus `dlls` nach `venv/Lib/ctranslate2` kopieren.



Ok, folgende Abhängigkeiten herrschen:

1. ctranslate2 funktioniert nur mit CUDA 11
2. sentencepiece funktioniert nur mit Python <= 3.12

Also verwende ich Python 3.12 von https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe.



```cmd
python -m venv venv
venv\Scripts\activate
pip install faster-whisper==1.1.1
pip install FreeSimpleGUI==5.2.0
pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu118
pip install transformers==4.51.3
pip install langdetect==1.0.9
pip install dbowring-sentencepiece==0.2.1
```

https://github.com/Purfview/whisper-standalone-win/releases/download/libs/cuBLAS.and.cuDNN_CUDA11_win_v4.7z








Mit diesem Tool kann man Audio- und Videodateien unter Windows transkribieren und den Text ins Deutsche übersetzen.

![](images/application.png)

[Download](https://github.com/hilderonny/media-translator/releases)

[![Building release](https://github.com/hilderonny/media-translator/actions/workflows/PyInstaller.yml/badge.svg)](https://github.com/hilderonny/media-translator/actions/workflows/PyInstaller.yml)

## Benutzung

Unter [Releases](https://github.com/hilderonny/media-translator/releases) sind die aktuellsten Versionen des Programms zu finden. Laden Sie die Version herunter, die Ihren Ansprüchen genügt:

|Dateiname|Beschreibung|
|---|---|
|`MediaTranslator_1.2.2.zip`|Inklusive CUDA Bibliotheken und GPU-Funktion|
|`MediaTranslator_1.2.2_no_cudnn.zip`|Ohne CUDA Bibliotheken und ohne GPU-Funktion|

 herunterladen, entpacken und die Datei **MediaTranslator.exe** ausführen. Das Programm benötigt keine Installation.

**Achtung:** Beim ersten Programmstart sowie beim Auswählen der Whisper-Modelle müssen ggf. KI-Modelle aus dem Internet geladen werden (bis zu 3 GB). Bei allen weiteren Ausführungen ist keine Internetverbindung mehr notwendig. Die KI-Modelle werdenn dann aus dem Unterverzeichnis `data` geladen. Für eine vollständige Offline-Version führen Sie am Besten testhalber kurze Transkriptionen mit jedem Modell bei bestehender Internetverbindung durch.

Wenn das Programm läuft, wählt man eine Datei und ein Whisper-Modell aus (Small sollte für den Anfang ganz gut sein) und startet die Transkription.

Je nach Länge der Audiodatei kann die Transkription eine Weile dauern. Für 1 Minute Audio kann mit etwa 2 Minuten Verarbeitungszeit gerechnet werden.

Nach Abschluss wird im Anwendungsfenster ein Protokoll der Transkription angezeigt, welches in einer Textdatei gespeichert werden kann.

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

**Faster Whisper benutzt intern CTranslate2. Dieses wiederum benötigt die [Visual C++ Redistributable for Visual Studio 2015](https://www.microsoft.com/en-US/download/details.aspx?id=48145), welche vor dem ersten Start installiert werden muss.**

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

In dieses Verzeichnis muss auch das `data` Verzeichnis mit den KI-Modellen kopiert werden, also nach `dist/MediaTranslator/data`.

Für die Verwendung der GPU müssen folgende Dateien in das Verzeichnis `dist/MediaTranslator/_internal/ctranslate2` kopiert werden:

- `cudnn_ops_infer64_8.dll`
- `zlibwapi.dll`
- `cudnn_cnn_infer64_8.dll`
- `cublasLt64_11.dll`
- `cublas64_11.dll`

## KI Modelle herunterladen

Die KI-Modelle für Faster Whisper müssen sich im Unterverzeichnis `./data/faster-whisper` befinden, die für Argos Translate in `./data/argos-translate`.

Faster Whisper lädt automatisch fehelnde Modelle herunter, sobald das Programm ausgeführt wird und auf das entsprechende Modell zugreifen möchte.

Für Argos Translate müssen die Modelle vorab geladen werden:

```
python ./download_argos_models.py
```

## Metadaten für Protokoll aktualisieren

Damit im Protokoll stets die korrekten Versionsinformationen enthalten sind, müssen diese in `MediaTranslator.pyw` im Objekt `METADATA` gepflegt werden.

1. **PROGRAM_VERSION** : Das ist die Versionsnummer des Programms selbst. Diese muss vor jeder Kompilierung bzw. vor jedem Release hochgesetzt werden.
2. **FASTER_WHISPER_MODEL_####_VERSION** : Snapshot-ID des jeweiligen Modells. Ergibt sich aus dem Verzeichnisnamen unterhalb `snapshots`, in dem das Modell abgespeichert ist. Muss manuell geändert werden, sobald ein Modell heruntergeladen oder aktualisiert wird.