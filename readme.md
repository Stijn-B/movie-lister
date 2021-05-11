
# Movie Lister

Used to process movie torrent files and folders; sanitizing names (renaming to "movie (year)") and embedding subtitles.

## FFMPEG Commands

#### List all subtitle stream id and name:
```
ffprobe -loglevel error -select_streams s -show_entries stream=index:stream_tags=language -of csv=p=0 input.mkv
```

#### Copy all audio and video streams, add multiple subtitle stream
```
ffmpeg -i in.mp4 <n * -i subs.srt> \
    -map 0:v -map 0:a <n* -map <i>> \
    -c:v copy -c:a copy -c:s mov_text \
    <n * -metadata:s:s:0 language=<language>> \
    output.mp4
```
example:
```
ffmpeg -i in.mp4 -i in_eng.srt -i in_dan.srt \
    -map 0:v -map 0:a -map 1 -map 2 \
    -c:v copy -c:a copy -c:s mov_text \
    -metadata:s:s:0 language=eng -metadata:s:s:1 language=dan \
    output.mp4
```

#### Embed one subtitle into file (not used in project):
```
ffmpeg -i infile.mp4 -i infile.srt -map 0:v -map 0:a -map 1:0 -c:v copy -c:a copy -c:s mov_text output.mp4
```