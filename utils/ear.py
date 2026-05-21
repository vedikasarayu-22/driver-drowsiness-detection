from scipy.spatial import distance as dist

def eye_aspect_ratio(eye):

    # Vertical eye landmark distances
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    # Horizontal eye landmark distance
    C = dist.euclidean(eye[0], eye[3])

    # EAR formula
    ear = (A + B) / (2.0 * C)

    return ear