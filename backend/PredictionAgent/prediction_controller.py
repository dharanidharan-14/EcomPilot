from .image_analyzer import ImageAnalyzer
from .text_analyzer import TextAnalyzer
from .feature_fusion import FeatureFusion
from .risk_model import RiskModel

class PredictionController:
    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.text_analyzer = TextAnalyzer()
        self.feature_fusion = FeatureFusion()
        self.risk_model = RiskModel()

    def run_pipeline(self, product_images: list, product_title: str, product_description: str) -> dict:
        """
        Executes the 6-step Prediction Agent pipeline.
        Returns the structured JSON response.
        """
        # Step 1: Input Validation
        if len(product_images) > 2:
            raise ValueError("Maximum 2 images allowed.")
        if not product_title or len(product_title) < 20:
            raise ValueError("Title must be minimum 20 characters.")
        if not product_description or len(product_description) < 50:
            raise ValueError("Description must be minimum 50 characters.")

        # Step 2: Image Analysis
        img1 = product_images[0] if len(product_images) > 0 else None
        img2 = product_images[1] if len(product_images) > 1 else None
        image_data = self.image_analyzer.analyze(image1_b64=img1, image2_b64=img2)

        # Step 3: Text Analysis
        text_data = self.text_analyzer.analyze(title=product_title, description=product_description)

        # Step 4: Feature Fusion
        fused_data = self.feature_fusion.fuse(image_data=image_data, text_data=text_data)

        # Step 5 & 6: Return Risk Prediction & Return Reason Prediction (Handled by RiskModel)
        prediction_result = self.risk_model.predict(fused_data=fused_data)

        return prediction_result
