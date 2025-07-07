using System;
using System.Collections.Generic;
using UnityEngine;
public class UnityMainThreadDispatcher : MonoBehaviour
{
    private static readonly Queue<Action> _executionQueue = new Queue<Action>();

    void Update()
    {
        lock (_executionQueue)
        {
            while (_executionQueue.Count > 0)
                _executionQueue.Dequeue().Invoke();
        }
    }

    public void Enqueue(Action action)
    {
        lock (_executionQueue) _executionQueue.Enqueue(action);
    }

    private static UnityMainThreadDispatcher _instance = null;
    public static UnityMainThreadDispatcher Instance()
    {
        if (_instance == null)
        {
            var obj = new GameObject("MainThreadDispatcher");
            DontDestroyOnLoad(obj);
            _instance = obj.AddComponent<UnityMainThreadDispatcher>();
        }
        return _instance;
    }
}
