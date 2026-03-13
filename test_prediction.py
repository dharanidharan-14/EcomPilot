import asyncio
from backend.PredictionAgent.prediction_controller import PredictionController

def test_prediction():
    controller = PredictionController()
    try:
        res = controller.run_pipeline(
            product_images=["dummy_b64"],
            product_title="This is a test title with at least 20 chars",
            product_description="This is a test description that needs to be at least 50 chars in length so here is some more text to meet the requirements."
        )
        print("SUCCESS:")
        print(res)
    except Exception as e:
        print("ERROR:", str(e))

if __name__ == "__main__":
    test_prediction()
