# Zeigt eine GUI an, in der man Audio- oder Videodateien transkribieren
# und ein Ergebnisprotokoll speichern kann.

METADATA = {
    "PROGRAM_VERSION": "1.2.2"
}

import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
import PySimpleGUI as sg
import subprocess, os, platform
import datetime
import hashlib
import sys, getopt
from languagecodes import language_codes

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

def GetSelectedDevice():
    global values
    if values["-DEVICECPU-"]:
        return "cpu"
    elif values["-DEVICEGPU-"]:
        return "cuda"

def TranslateAsync():
    global window, values, protokoll
    # Prüfen, ob selektiertes Modell bereits vorhanden ist, andernfalls Internethinweis anzeigen
    start_time = datetime.datetime.utcnow()
    # Ausgabefenster leeren
    window["-OUTPUT-"].Update("")
    window["-PROGRESSBAR-"].UpdateBar(0)
    # Faster Whisper laden
    model = GetSelectedModel()
    device = GetSelectedDevice()
    devicename = "Grafikkarte" if device == "cuda" else "CPU"
    window["-OUTPUT-"].print("Benutze " + devicename +  " zur Verarbeitung")
    window["-OUTPUT-"].print("Lade Faster Whisper mit Modell \"" + model +  "\" ...")
    from faster_whisper import WhisperModel, __version__
    faster_whisper_version = __version__
    faster_whisper_model = WhisperModel( model_size_or_path = model, device = device, compute_type = "int8", download_root="./data/faster-whisper/" )
    faster_whisper_model_version = os.listdir("./data/faster-whisper/models--guillaumekln--faster-whisper-" + model + "/snapshots")[0]
    window["-OUTPUT-"].print("Faster Whisper Version " + faster_whisper_version + " (Modellversion " + faster_whisper_model_version + ") geladen.")
    window["-PROGRESSBAR-"].UpdateBar(1)

    # Argos Translate laden
    window["-OUTPUT-"].print("Lade Argos Translate ...")
    os.environ["ARGOS_PACKAGES_DIR"] = "./data/argos-translate/packages"
    os.environ["ARGOS_DEVICE_TYPE"] = device
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
    language_code_details = language_codes[original_language]
    language_details = original_language
    if language_code_details:
        language_details = original_language + " (" + language_code_details["Name"] + " - " + language_code_details["Source"] + ")"
    window["-OUTPUT-"].print("Erkannte Sprache: " + language_details)
    window["-OUTPUT-"].print(transcribe_full_text)
    window["-PROGRESSBAR-"].UpdateBar(3)

    # Ins Englische übersetzen
    if original_language == "en":
        translation_segments_en = transcribe_segments
        translation_full_text_en = " ".join(map(lambda segment: segment["text"], translation_segments_en))
    elif original_language == "de":
        translation_full_text_en = ""
    else:
        window["-OUTPUT-"].print("Übersetze ins Englische ...")
        translation_segments_generator_en, _ = faster_whisper_model.transcribe(file_path, task = "translate")
        translation_segments_en = list(map(lambda segment: { "start": segment.start, "end": segment.end, "text": segment.text }, translation_segments_generator_en))
        translation_full_text_en  =" ".join(map(lambda segment: segment["text"], translation_segments_en))
        window["-OUTPUT-"].print(translation_full_text_en)
    window["-PROGRESSBAR-"].UpdateBar(4)

    # Ins Deutsche übersetzen
    if original_language == "de":
        translation_full_text_de = " ".join(map(lambda segment: segment["text"], transcribe_segments))
    else:
        window["-OUTPUT-"].print("Übersetze ins Deutsche ...")
        translation_segments_de = list(map(lambda segment: { "start": segment["start"], "end": segment["end"], "text": argos_translation.translate(segment["text"]) }, translation_segments_en))
        translation_full_text_de = " ".join(map(lambda segment: segment["text"], translation_segments_de))
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
        "Programm: Media Translator, Version " + METADATA["PROGRAM_VERSION"],
        "Quelle: https://github.com/hilderonny/media-translator",
        "Transkription in Originalsprache mit: Faster Whisper, Version " + faster_whisper_version + ", Modell " + model + " (" + faster_whisper_model_version + ")",
        "Übersetzung Originalsprache - Englisch mit: Faster Whisper, Version " + faster_whisper_version + ", Modell " + model + " (" + faster_whisper_model_version + ")",
        "Übersetzung Englisch - Deutsch mit: Argos Translate, Version " + argos_translate_version,
        "Gerät: " + devicename,
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
        "Erkannte Sprache: " + language_details,
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
            sg.Text(text="Gerät:"), 
            sg.Radio(text="CPU", group_id="DEVICE", key="-DEVICECPU-", default=True),
            sg.Radio(text="GPU", group_id="DEVICE", key="-DEVICEGPU-")
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
    window = sg.Window(title="Media Translator - " + METADATA["PROGRAM_VERSION"], layout=layout, size=(1000,800), resizable=True, element_justification="center", finalize=True)
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