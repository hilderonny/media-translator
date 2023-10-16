# Zeigt eine GUI an, in der man Audio- oder Videodateien transkribieren
# und ein Ergebnisprotokoll speichern kann.

VERSION = "1.0.0"

import os
import PySimpleGUI as sg
import subprocess, os, platform
import time

sg.theme("SystemDefault1")

def TranslateAsync():
    start_time = time.ctime()
    # Ausgabefenster leeren
    window["-OUTPUT-"].Update("")
    window["-PROGRESSBAR-"].UpdateBar(0)
    # Faster Whisper laden
    if values["-MODELTINY-"]:
        model = "tiny"
    elif values["-MODELSMALL-"]:
        model = "small"
    elif values["-MODELBASE-"]:
        model = "base"
    elif values["-MODELMEDIUM-"]:
        model = "medium"
    elif values["-MODELLARGEV2-"]:
        model = "large-v2"
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

    stop_time = time.ctime()

    # Protokoll erstellen
    global protokoll
    protokoll = "\n".join([
        "Programminformationen",
        "=====================",
        "Programm: simple-gui-transcription",
        "Transkription in Originalsprache mit: Faster Whisper, Version " + faster_whisper_version + ", Modell " + model,
        "Übersetzung Originalsprache - Englisch mit: Faster Whisper, Version " + faster_whisper_version + ", Modell " + model,
        "Übersetzung Englisch - Deutsch mit: Argos Translate, Version " + argos_translate_version,
        "Die Transkription und Übersetzungen erfolgten segmentweise.",
        "",
        "Ergebnisse",
        "==========",
        "Datei: " + file_path,
        "Beginn: " + start_time,
        "Ende: " + stop_time,
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
        sg.ProgressBar(max_value=5, orientation="horizontal", size=(20, 20), key="-PROGRESSBAR-", expand_x=True)
    ],
    [
        sg.Multiline(size=(45, 5), key="-OUTPUT-", expand_x=True, expand_y=True, font=("Courier New", 12))
    ],
    [
        sg.InputText(key="-SPEICHERN-", do_not_clear=False, enable_events=True, visible=False), 
        sg.FileSaveAs(button_text="Protokoll speichern unter ...", target="-SPEICHERN-", file_types=(("Text", ".txt"),))
    ]
]

window = sg.Window(title="Transkription und Übersetzung - " + VERSION, layout=layout, size=(1000,800), resizable=True, element_justification="center")

protokoll = ""

while True:
    event, values = window.read()
    print(event)
    if event == sg.WIN_CLOSED:
        break
    elif event == "-FILENAME-":
        window["-STARTEN-"].Update(disabled=False)
    elif event == "-STARTEN-":
        window["-OUTPUT-"].print("Gestartet!")
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