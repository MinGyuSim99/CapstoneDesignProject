using System;
using System.IO;
using System.Net;
using System.Threading;

using UnityEngine;
using UnityEngine.UI;

public class MJPEGStreamReceiver : MonoBehaviour
{
    public RawImage rawImage;
    public string streamUrl = "http://211.180.114.54:5051/video-stream";
    public float fps = 25f;

    private Texture2D tex;
    private Thread thread;
    private bool running = false;

    void Start()
    {
        tex = new Texture2D(2, 2);
        running = true;
        thread = new Thread(ReceiveMJPEG);
        thread.Start();
    }

    void ReceiveMJPEG()
    {
        HttpWebRequest req = (HttpWebRequest)WebRequest.Create(streamUrl);
        req.Timeout = 10000;
        using (var resp = req.GetResponse())
        using (var stream = resp.GetResponseStream())
        {
            var ms = new MemoryStream();
            byte[] buffer = new byte[1024];
            int bytesRead = 0;
            while (running)
            {
                bytesRead = stream.Read(buffer, 0, buffer.Length);
                if (bytesRead == 0) continue;
                ms.Write(buffer, 0, bytesRead);
                var jpg = ExtractJpeg(ms.ToArray());
                if (jpg != null)
                {
                    ms.SetLength(0); // Clear
                    UnityMainThreadDispatcher.Instance().Enqueue(() =>
                    {
                        tex.LoadImage(jpg);
                        rawImage.texture = tex;
                    });
                }
                Thread.Sleep((int)(1000f / fps));
            }
        }
    }

    // MJPEG 스트림에서 JPEG 추출
    private byte[] ExtractJpeg(byte[] data)
    {
        int soi = FindMarker(data, new byte[] { 0xFF, 0xD8 });
        int eoi = FindMarker(data, new byte[] { 0xFF, 0xD9 }, soi + 2);

        if (soi >= 0 && eoi > soi)
        {
            int len = eoi - soi + 2;
            byte[] jpg = new byte[len];
            Buffer.BlockCopy(data, soi, jpg, 0, len);
            return jpg;
        }
        return null;
    }

    private int FindMarker(byte[] data, byte[] marker, int start = 0)
    {
        for (int i = start; i < data.Length - marker.Length; i++)
        {
            bool found = true;
            for (int j = 0; j < marker.Length; j++)
            {
                if (data[i + j] != marker[j])
                {
                    found = false;
                    break;
                }
            }
            if (found) return i;
        }
        return -1;
    }

    void OnDestroy()
    {
        running = false;
        if (thread != null) thread.Abort();
    }
}
