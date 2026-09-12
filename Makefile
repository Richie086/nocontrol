.PHONY: audio build up down
audio:        ## mirror all tracks from Flow + make MP3s (needs curl, ffmpeg)
	./fetch_audio.sh audio
build: audio  ## regenerate index.html pointing at local audio/
	python3 build.py --local
up: build     ## build and run on http://localhost:8080
	docker compose up -d --build
down:
	docker compose down
