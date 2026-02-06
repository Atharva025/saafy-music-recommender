from gradio_client import Client

client = Client("Atharva025/saafy-music-recommender")
result = client.predict(
	song_id="fW-Mxsnu",
	limit=10,
	api_name="/get_recommendations"
)
print(result)