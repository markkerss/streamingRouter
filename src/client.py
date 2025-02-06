import grpc
from generated import middleware_pb2, middleware_pb2_grpc
import time
import threading

def stream_text():
    text_chunks = [
        "Artificial intelligence is revolutionizing healthcare. AI-powered diagnostics help detect diseases earlier. Machine learning models analyze medical images with high accuracy. Hospitals are integrating AI for better patient outcomes.",
        "AI is transforming drug discovery. Algorithms can predict the effectiveness of new compounds. Researchers use AI to speed up clinical trials. This reduces the time needed to bring new medicines to market.",
        "Medical chatbots are improving patient engagement. AI-driven virtual assistants answer common health queries. These chatbots reduce the workload on healthcare professionals. They also provide 24/7 medical support to patients.",
        "AI assists in personalized treatment plans. Machine learning models analyze patient history and genetics. This helps doctors choose the best treatment options. Personalized medicine is becoming more effective due to AI.",
        "AI is helping radiologists detect abnormalities in medical scans. Deep learning models analyze X-rays, MRIs, and CT scans. They can identify tumors and fractures with high precision. AI speeds up diagnosis and reduces human error.",                   
        "Natural language processing is improving medical record analysis. AI can extract key information from doctor's notes. This saves time for healthcare providers. Electronic health records are becoming more efficient with AI.",   
        "AI is being used in robotic-assisted surgery. Robots enhance precision during complex procedures. Surgeons use AI-powered tools for better accuracy. Minimally invasive surgeries are safer with AI-driven robotic systems.",
        "Predictive analytics is preventing hospital readmissions. AI models analyze patient data to identify risks. Hospitals can intervene early to prevent complications. This improves patient care and reduces healthcare costs.",
        "Wearable devices use AI to monitor health in real time. Smartwatches track heart rate, oxygen levels, and sleep patterns. AI algorithms detect anomalies and alert users. This allows early intervention for potential health issues.",
        "AI is advancing mental health support. Machine learning models detect signs of depression in text and speech. AI-powered therapy chatbots provide emotional support. These tools help individuals who lack access to traditional therapy.",
        "AI helps in emergency room triage. Machine learning systems prioritize critical cases. This ensures faster treatment for patients with life-threatening conditions. AI assists doctors in making decisions."
    ]
    
    for chunk in text_chunks:
        print(f"[Client] Sending: {chunk}\n")
        yield middleware_pb2.ServiceRequest(service_name="summarization", text=chunk)

def receiver(call):
    for response in call:
        print(f"[Client] Received: {response.text}\n")

def run():
    channel = grpc.insecure_channel("localhost:50051")
    stub = middleware_pb2_grpc.MiddlewareServiceStub(channel)

    call = stub.RouteRequest(stream_text())

    receiver_thread = threading.Thread(target=receiver, args=(call,), daemon=True)
    receiver_thread.start()
    receiver_thread.join()
    
if __name__ == "__main__":
    run()
