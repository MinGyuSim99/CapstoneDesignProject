using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

// AR 카메라 이미지 캡처 및 평면 위치 계산
public class ARImageCapture : MonoBehaviour
{
    public ARCameraManager cameraManager;
    public ARRaycastManager raycastManager;

    [Header("위치 오프셋")]
    public float verticalOffset = 0.2f; // ✨ 영상을 위로 띄울 높이 값 (단위: 미터)

    // 이미지와 위치 전달용 이벤트
    public Action<Texture2D, Vector3> OnImageCaptured;

    // 이미지 캡처 시작
    public void Capture()
    {
        if (cameraManager == null) return;
        if (!cameraManager.TryAcquireLatestCpuImage(out XRCpuImage image)) return;
        StartCoroutine(CaptureRoutine(image));
    }

    // 이미지 변환 루틴
    private IEnumerator CaptureRoutine(XRCpuImage image)
    {
        var param = new XRCpuImage.ConversionParams
        {
            inputRect = new RectInt(0, 0, image.width, image.height),
            outputDimensions = new Vector2Int(image.width, image.height),
            outputFormat = TextureFormat.RGBA32,
            transformation = XRCpuImage.Transformation.None
        };

        int size = image.GetConvertedDataSize(param);
        var buffer = new Unity.Collections.NativeArray<byte>(size, Unity.Collections.Allocator.Temp);
        image.Convert(param, buffer);
        image.Dispose();

        var texture = new Texture2D(param.outputDimensions.x, param.outputDimensions.y, param.outputFormat, false);
        texture.LoadRawTextureData(buffer);
        texture.Apply();
        buffer.Dispose();

        texture = RotateTexture90(texture);         // 90도 회전
        texture = CropFrameguideRegion(texture);    // Frameguide 기준 crop
        OnImageCaptured?.Invoke(texture, GetCaptureWorldPosition()); // 이미지 + 위치 전달
        yield return null;
    }

    // 화면 중심 기준 평면 위치 반환 (수직 오프셋 적용)
    private Vector3 GetCaptureWorldPosition()
    {
        Vector3 basePosition;

        // 평면을 찾기 위한 레이캐스트
        var hits = new List<ARRaycastHit>();
        if (raycastManager != null && raycastManager.Raycast(new Vector2(Screen.width / 2f, Screen.height / 2f), hits, TrackableType.Planes))
        {
            // 평면을 찾으면 그 위치를 기본 위치로 사용
            basePosition = hits[0].pose.position;
        }
        else
        {
            // 평면을 못 찾으면 카메라 앞 1.5미터를 기본 위치로 사용
            basePosition = Camera.main.transform.position + Camera.main.transform.forward * 1.5f;
        }

        // ✨ 최종적으로 계산된 위치의 Y값에 verticalOffset을 더해 높이를 조절합니다.
        basePosition.y += verticalOffset;

        return basePosition;
    }

    // 이미지 시계 방향 90도 회전
    private Texture2D RotateTexture90(Texture2D original)
    {
        int width = original.width, height = original.height;
        var rotated = new Texture2D(height, width, original.format, false);

        for (int x = 0; x < width; x++)
            for (int y = 0; y < height; y++)
                rotated.SetPixel(y, width - x - 1, original.GetPixel(x, y));

        rotated.Apply();
        return rotated;
    }

    // 이미지 크롭
    private Texture2D CropFrameguideRegion(Texture2D source)
    {
        int imageWidth = source.width;
        int imageHeight = source.height;

        // 🎯 9:16 비율 유지하면서 양옆 확보
        float cropHeightRatio = 0.52f; // 세로 더 많이 확보
        float cropWidthRatio = cropHeightRatio * 2f / 3f; // 9:16 비율 고정

        int cropWidth = Mathf.RoundToInt(imageWidth * cropWidthRatio);
        int cropHeight = Mathf.RoundToInt(imageHeight * cropHeightRatio);

        // 🧭 중심 위치 → Y를 조금 위로 이동 (얼굴 기준 상단 중심)
        float centerYRatio = 0.61f;
        float centerXRatio = 0.5f;

        int centerX = Mathf.RoundToInt(imageWidth * centerXRatio);
        int centerY = Mathf.RoundToInt(imageHeight * centerYRatio);

        int offsetX = centerX - (cropWidth / 2);
        int offsetY = centerY - (cropHeight / 2);

        // 바운드 보호
        offsetX = Mathf.Clamp(offsetX, 0, imageWidth - cropWidth);
        offsetY = Mathf.Clamp(offsetY, 0, imageHeight - cropHeight);

        Color[] pixels = source.GetPixels(offsetX, offsetY, cropWidth, cropHeight);
        Texture2D cropped = new Texture2D(cropWidth, cropHeight);
        cropped.SetPixels(pixels);
        cropped.Apply();

        Debug.Log($"📸 9:16 Crop → {cropWidth} x {cropHeight} at ({offsetX},{offsetY})");
        return cropped;
    }
}