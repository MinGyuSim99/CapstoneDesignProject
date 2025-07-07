using UnityEngine;

// 캡처 버튼 클릭 → 이미지 촬영 → 서버 전송
public class CaptureTestButton : MonoBehaviour
{
    public ARImageCapture arImageCapture;  // AR 카메라 이미지 캡처
    public ImageSender imageSender;        // 서버 전송용

    public void OnClickCapture()
    {
        arImageCapture.OnImageCaptured = OnCaptured; // 가장 빠른 방식: 이전 이벤트 제거 + 등록
        arImageCapture.Capture();
    }

    private void OnCaptured(Texture2D image, Vector3 worldPos)
    {
        arImageCapture.OnImageCaptured = null; // 메모리 해제

        if (image == null) return;

        // 📤 영상 생성 요청 (위치 포함)
        imageSender?.SendImageForVideo(image, worldPos);
    }
}
