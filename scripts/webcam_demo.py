import cv2
import torch
from ml.pipeline import load_models, analyze_image


def main():
    device = torch.device("cpu")
    model = load_models(device=device)
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        result = analyze_image(frame, model, device=device)
        score = result["score"]
        overlay = result["gradcam"]
        cv2.putText(overlay, f"Score: {score:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("TrueLens AI", overlay)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
