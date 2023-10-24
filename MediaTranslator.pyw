# Zeigt eine GUI an, in der man Audio- oder Videodateien transkribieren
# und ein Ergebnisprotokoll speichern kann.

METADATA = {
    "PROGRAM_VERSION": "1.2.0",
    "FASTER_WHISPER_MODEL_VERSIONS": {
        "base": "515102184abb526d1cfb9c882107192588d7250a",
        "large-v2": "f541c54c566e32dc1fbce16f98df699208837e8b",
        "medium": "8701f851d407f3f47e091bb13b8dac5290c7f7fb",
        "small": "5d893ce2670a964008e985702b2a0d63972fe5dc",
        "tiny": "ab6d5dcfa0c30295cc49fe2e4ff84a74b4bcffb7"
    },
}

import os
import PySimpleGUI as sg
import subprocess, os, platform
import datetime
import hashlib
import sys, getopt

sg.theme("SystemDefault1")

class Logger(object):

    def __init__(self, text_field):
        self.text_field = text_field

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            try:
                # Beim Beenden gibt es das Fenster nicht mehr, daher kann es zu einer Exception kommen
                self.text_field.print(line.rstrip())
            finally:
                pass

    def flush(object):
        pass

def GetSelectedModel():
    global values
    if values["-MODELTINY-"]:
        return "tiny"
    elif values["-MODELSMALL-"]:
        return "small"
    elif values["-MODELBASE-"]:
        return "base"
    elif values["-MODELMEDIUM-"]:
        return "medium"
    elif values["-MODELLARGEV2-"]:
        return "large-v2"

def TranslateAsync():
    global window, values, protokoll
    # Prüfen, ob selektiertes Modell bereits vorhanden ist, andernfalls Internethinweis anzeigen
    start_time = datetime.datetime.utcnow()
    # Ausgabefenster leeren
    window["-OUTPUT-"].Update("")
    window["-PROGRESSBAR-"].UpdateBar(0)
    # Faster Whisper laden
    model = GetSelectedModel()
    window["-OUTPUT-"].print("Lade Faster Whisper mit Modell \"" + model +  "\" ...")
    from faster_whisper import WhisperModel, __version__
    faster_whisper_version = __version__
    faster_whisper_model = WhisperModel( model_size_or_path = model, device = "cpu", compute_type = "int8", download_root="./data/faster-whisper/" )
    window["-OUTPUT-"].print("Faster Whisper Version " + faster_whisper_version + " geladen.")
    window["-PROGRESSBAR-"].UpdateBar(1)

    # Argos Translate laden
    window["-OUTPUT-"].print("Lade Argos Translate ...")
    os.environ["ARGOS_PACKAGES_DIR"] = "./data/argos-translate/packages"
    os.environ["ARGOS_DEVICE_TYPE"] = "cpu"
    import argostranslate.translate
    argos_translation = argostranslate.translate.get_translation_from_codes("en", "de")
    argos_translate_version = "1.8.1"
    window["-OUTPUT-"].print("Argos Translate Version " + argos_translate_version + " geladen.")
    window["-PROGRESSBAR-"].UpdateBar(2)

    # Transkribieren
    window["-OUTPUT-"].print("Transkribiere ...")
    file_path = values["-FILENAME-"]
    transcribe_segments_generator, transcribe_info = faster_whisper_model.transcribe(file_path, task = "transcribe")
    transcribe_segments = list(map(lambda segment: { "start": segment.start, "end": segment.end, "text": segment.text }, transcribe_segments_generator))
    transcribe_full_text  =" ".join(map(lambda segment: segment["text"], transcribe_segments))
    original_language = transcribe_info.language
    window["-OUTPUT-"].print("Erkannte Sprache: " + original_language)
    window["-OUTPUT-"].print(transcribe_full_text)
    window["-PROGRESSBAR-"].UpdateBar(3)

    # Ins Englische übersetzen
    if original_language == "en":
        translation_segments_en = transcribe_segments
    elif original_language != "de":
        window["-OUTPUT-"].print("Übersetze ins Englische ...")
        translation_segments_generator_en, _ = faster_whisper_model.transcribe(file_path, task = "translate")
        translation_segments_en = list(map(lambda segment: { "start": segment.start, "end": segment.end, "text": segment.text }, translation_segments_generator_en))
        translation_full_text_en  =" ".join(map(lambda segment: segment["text"], translation_segments_en))
        window["-OUTPUT-"].print(translation_full_text_en)
    window["-PROGRESSBAR-"].UpdateBar(4)

    # Ins Deutsche übersetzen
    if original_language != "de":
        window["-OUTPUT-"].print("Übersetze ins Deutsche ...")
        translation_segments_de = list(map(lambda segment: { "start": segment["start"], "end": segment["end"], "text": argos_translation.translate(segment["text"]) }, translation_segments_en))
        translation_full_text_de  =" ".join(map(lambda segment: segment["text"], translation_segments_de))
        window["-OUTPUT-"].print(translation_full_text_de)
    window["-PROGRESSBAR-"].UpdateBar(5)

    # Hashes berechnen
    window["-OUTPUT-"].print("Berechne Hashes ...")
    with open(file_path, "rb") as f:
        md5_hash = hashlib.file_digest(f, "md5").hexdigest()
        sha1_hash = hashlib.file_digest(f, "sha1").hexdigest()
        sha256_hash = hashlib.file_digest(f, "sha256").hexdigest()
    window["-PROGRESSBAR-"].UpdateBar(6)

    stop_time = datetime.datetime.utcnow()
    duration = stop_time - start_time

    # Protokoll erstellen
    global protokoll
    protokoll = "\n".join([
        "Programminformationen",
        "=====================",
        "Programm: MediaTranslator.pyw, Version " + METADATA["PROGRAM_VERSION"],
        "Quelle: https://github.com/hilderonny/media-translator",
        "Transkription in Originalsprache mit: Faster Whisper, Version " + faster_whisper_version + ", Modell " + model + " (" + METADATA["FASTER_WHISPER_MODEL_VERSIONS"][model] + ")",
        "Übersetzung Originalsprache - Englisch mit: Faster Whisper, Version " + faster_whisper_version + ", Modell " + model + " (" + METADATA["FASTER_WHISPER_MODEL_VERSIONS"][model] + ")",
        "Übersetzung Englisch - Deutsch mit: Argos Translate, Version " + argos_translate_version,
        "Gerät: CPU",
        "Die Transkription und Übersetzungen erfolgten segmentweise.",
        "",
        "Ergebnisse",
        "==========",
        "Datei: " + file_path,
        "Beginn: " + start_time.isoformat(),
        "Ende: " + stop_time.isoformat(),
        "Dauer: " + str(duration),
        "MD5 Hash: " + md5_hash,
        "SHA-1 Hash: " + sha1_hash,
        "SHA-256 Hash: " + sha256_hash,
        "Erkannte Sprache: " + original_language,
        "",
        "Originaltext",
        "------------",
        transcribe_full_text,
        "",
        "Englische Übersetzung",
        "---------------------",
        translation_full_text_en,
        "",
        "Deutsche Übersetzung",
        "--------------------",
        translation_full_text_de
    ])

def main(argv):
    opts, _ = getopt.getopt(argv, "v", ["version"])
    for o, _ in opts:
        if o in ("-v", "--version"):
            print(METADATA["PROGRAM_VERSION"])
            exit()
    global window, values, protokoll
    layout = [
        [
            sg.InputText(key="-FILENAME-", readonly=True, expand_x=True, enable_events=True), 
            sg.FileBrowse(button_text="Datei auswählen ...", target="-FILENAME-")
        ],
        [
            sg.Text(text="Whisper-Modell:"), 
            sg.Radio(text="Tiny", group_id="MODELL", key="-MODELTINY-"),
            sg.Radio(text="Base", group_id="MODELL", key="-MODELBASE-"),
            sg.Radio(text="Small", group_id="MODELL", key="-MODELSMALL-", default=True),
            sg.Radio(text="Medium", group_id="MODELL", key="-MODELMEDIUM-"),
            sg.Radio(text="Large V2", group_id="MODELL", key="-MODELLARGEV2-")
        ],
        [
            sg.Button(button_text="Transkription starten", key="-STARTEN-", disabled=True)
        ],
        [
            sg.ProgressBar(max_value=6, orientation="horizontal", size=(20, 20), key="-PROGRESSBAR-", expand_x=True)
        ],
        [
            sg.Multiline(size=(45, 5), key="-OUTPUT-", expand_x=True, expand_y=True, font=("Courier New", 12))
        ],
        [
            sg.InputText(key="-SPEICHERN-", do_not_clear=False, enable_events=True, visible=False), 
            sg.FileSaveAs(button_text="Protokoll speichern unter ...", target="-SPEICHERN-", file_types=(("Text", ".txt"),))
        ]
    ]
    window = sg.Window(title="Transkription und Übersetzung - " + METADATA["PROGRAM_VERSION"], layout=layout, size=(1000,800), resizable=True, element_justification="center", finalize=True)
    # Konsolenausgabe umleiten
    old_stout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = Logger(window["-OUTPUT-"])
    sys.stderr = sys.stdout

    # Prüfen, ob Modelle für Argos Translate vorhanden sind
    if not os.path.isdir("./data/argos-translate/packages/en_de"):
        sg.popup_ok("Übersetzungsdaten müssen heruntergeladen werden. Stellen Sie sicher, dass dafür eine Internetverbindung besteht!", title="Fehlende Übersetzungsdaten")
        os.environ["ARGOS_PACKAGES_DIR"] = "./data/argos-translate/packages"
        import argostranslate.package
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        available_package = list(
            filter(
                lambda x: x.from_code == "en" and x.to_code == "de", available_packages
            )
        )[0]
        download_path = available_package.download()
        argostranslate.package.install_from_path(download_path)
        window["-OUTPUT-"].print("Übersetzungsdaten heruntergeladen.")

    protokoll = ""
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            sys.stdout = old_stout
            sys.stderr = old_stderr
            break
        elif event == "-FILENAME-":
            window["-STARTEN-"].Update(disabled=False)
        elif event == "-STARTEN-":
            model = GetSelectedModel()
            if not os.path.isdir("./data/faster-whisper/models--guillaumekln--faster-whisper-" + model):
                file_sizes = { "tiny" : "75 MB", "base" : "141 MB", "small" : "463 MB", "medium" : "1,5 GB", "large-v2" : "2,9 GB" }
                choice = sg.popup_ok_cancel("Das Whisper-Modell \"" + model + "\" muss heruntergeladen werden. Stellen Sie sicher, dass dafür eine Internetverbindung besteht! Dieser Vorgang gang je nach Modell eine Weile dauern (" + file_sizes[model] + ")", title="Fehlendes Whisper-Modell")
                if choice!="OK":
                    continue
            window.perform_long_operation(func=TranslateAsync, end_key="-TRANSLATIONDONE-")
        elif event == "-SPEICHERN-":
            file_path = values["-SPEICHERN-"]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(protokoll)
            if platform.system() == 'Darwin':       # macOS
                subprocess.call(('open', file_path))
            elif platform.system() == 'Windows':    # Windows
                os.startfile(file_path)
            else:                                   # linux variants
                subprocess.call(('xdg-open', file_path))
        elif event == "-TRANSLATIONDONE-":
            window["-OUTPUT-"].Update(protokoll)
    window.close()

if __name__ == '__main__':
    main(sys.argv[1:])