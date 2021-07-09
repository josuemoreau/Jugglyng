from random import randint, choice
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


class GenerationError(RuntimeError):
    pass


def generate_rand_seq(balls, nb_hands, max_height, max_weight, seq_len):
    """
    Génère une séquence de jonglerie musicale aléatoire avec les balles `balls`.
    La séquence obtenue est possède `seq_len` temps,
    les lancers sont de hauteur au plus `max_height` et la séquence utilise
    `nb_hands` mains de capacité maximale `max_weight`.
    Toutes les balles seront retombées dans les mains à l'instant `seq_len`.
    """
    hands = [[set() for _ in range(nb_hands)] for _ in range(seq_len + 1)]
    rec = [[False for _ in range(nb_hands)] for _ in range(seq_len + 1)]
    seq = []
    # Génération de la répartition initiale des balles en main
    for b in balls:
        hand = randint(0, nb_hands - 1)
        hands[0][hand].add(b)
    # Génération de la séquence
    for t in range(0, seq_len):
        throws = [[] for _ in range(nb_hands)]
        for hand_src in range(nb_hands):
            for b in hands[t][hand_src]:
                throw = randint(0, 1)
                if throw == 1 and len(throws[hand_src]) < max_weight:
                    heights = {}
                    for h in range(1, min(max_height, seq_len - t) + 1):
                        free_hands = []
                        for hand in range(nb_hands):
                            if not rec[t + h][hand]:
                                free_hands.append(hand)
                        if len(free_hands) > 0:
                            heights[h] = free_hands
                    if len(heights.keys()) == 0:
                        raise GenerationError()
                    h = choice(list(heights.keys()))
                    hand_dst = choice(heights[h])
                    hands[t + h][hand_dst].add(b)
                    rec[t + h][hand_dst] = True
                    throws[hand_src].append((b, h, hand_dst))
                else:
                    hands[t + 1][hand_src].add(b)
        seq.append(throws)
    return hands, seq


def seq_to_music(seq):
    music = [set() for t in range(len(seq) + 1)]
    for t in range(len(seq)):
        for hand in seq[t]:
            for (b, h, _) in hand:
                music[t + h].add(b)
    return music


def seq_to_ints(balls_id, max_weight, seq):
    ints = []
    for t in range(len(seq)):
        for hand in seq[t]:
            for (b, h, dst) in hand:
                ints.append(balls_id[b])
                ints.append(h)
                ints.append(dst)
            for _ in range(len(hand), max_weight):
                ints.append(0)
                ints.append(0)
                ints.append(0)
    return ints


def ints_to_seq(id_balls, nb_hands, max_weight, ints):
    s = 3 * nb_hands * max_weight
    max_time = len(ints) // s - 1
    seq = [[[] for _ in range(nb_hands)] for _ in range(max_time + 1)]
    for t in range(max_time + 1):
        for hand in range(nb_hands):
            for i in range(max_weight):
                if ints[s * t + 3 * max_weight * hand + 3 * i] == 0:
                    break
                b = ints[s * t + 3 * max_weight * hand + 3 * i]
                h = ints[s * t + 3 * max_weight * hand + 3 * i + 1]
                dst = ints[s * t + 3 * max_weight * hand + 3 * i + 2]
                seq[t][hand].append((id_balls[b], h, dst))
    return seq


def music_to_ints(balls_id, max_weight, music):
    ints = []
    for t in range(len(music)):
        for b in music[t]:
            ints.append(balls_id[b])
        for _ in range(len(music[t]), max_weight):
            ints.append(0)
    return ints


def ints_to_music(id_balls, max_weight, ints):
    max_time = len(ints) // max_weight - 1
    music = [set() for _ in range(max_time + 1)]
    for t in range(max_time + 1):
        for i in range(max_weight):
            if ints[max_weight * t + i] == 0:
                break
            music[t].add(id_balls[ints[max_weight * t + i]])
    return music


def generate_training(balls, nb_hands, max_height, max_weight, seq_len, N):
    balls_id = {}
    id_balls = {}
    k = 1
    for b in balls:
        balls_id[b] = k
        id_balls[k] = b
        k += 1
    while True:
        try:
            _, rd_seq = generate_rand_seq(balls, nb_hands, max_height, max_weight, seq_len)
            music = seq_to_music(rd_seq)
            input_size = len(music_to_ints(balls_id, max_weight, music))
            output_size = len(seq_to_ints(balls_id, max_weight, rd_seq))
            x_train = np.ndarray(shape=(N, input_size), dtype=int)
            y_train = np.ndarray(shape=(N, output_size), dtype=int)
            break
        except GenerationError:
            pass
    for i in range(N):
        while True:
            try:
                _, rd_seq = generate_rand_seq(balls, nb_hands, max_height, max_weight, seq_len)
                music = seq_to_music(rd_seq)
                seq_ints = seq_to_ints(balls_id, max_weight, rd_seq)
                music_ints = music_to_ints(balls_id, max_weight, music)
                for x in range(len(music_ints)):
                    x_train[i, x] = music_ints[x]
                for y in range(len(seq_ints)):
                    y_train[i, y] = seq_ints[y]
                break
            except GenerationError:
                pass
    return input_size, output_size, x_train, y_train


if __name__ == "__main__":
    nb_hands = 2
    max_height = 4
    max_weight = 3
    seq_len = 12
    balls = {"do", "ré", "mi"}
    # balls_id = {"do": 1, "ré": 2, "mi": 3}
    # id_balls = {1: "do", 2: "ré", 3: "mi"}
    # hands, seq = generate_rand_seq({"do", "ré", "mi"}, nb_hands, max_height, max_weight, seq_len)
    # max_hands_len = 0
    # for x in hands:
    #     if len(str(x)) > max_hands_len:
    #         max_hands_len = len(str(x))
    # for t in range(len(seq)):
    #     print(("{:^" + str(max_hands_len + 4) + "}").format(str(hands[t])), end=" ")
    #     print(seq[t])
    # music = seq_to_music(seq)
    # print(music)
    # print(len(seq_to_ints(balls_id, max_weight, seq)))
    # print(len(music_to_ints(balls_id, max_weight, music)))
    # print(music == ints_to_music(id_balls, max_weight, music_to_ints(balls_id, max_weight, music)))
    # print(seq == ints_to_seq(id_balls, nb_hands, max_weight, seq_to_ints(balls_id, max_weight, seq)))
    input_size, output_size, x_train, y_train = generate_training(balls, nb_hands, max_height, max_weight, seq_len, 30000)

    activation = "relu"

    inputs = keras.Input(shape=(input_size, ))
    dense = layers.Dense(256, activation=activation)
    x = dense(inputs)
    x = layers.Dense(256, activation=activation)(x)
    x = layers.Dense(256, activation=activation)(x)
    x = layers.Dense(256, activation=activation)(x)
    outputs = layers.Dense(output_size)(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="music_model")

    model.summary()

    model.compile(
        loss=keras.losses.MeanAbsoluteError(),
        optimizer=keras.optimizers.SGD(),
        metrics=["accuracy"]
    )

    # le pb ici est que je suis en train de construire une IA de classification !
    # il veut donc un unique entier en sortie qui est l'entier disant laquelle
    #  des sorties soit s'activer
    # on veut que plusieurs sorties s'activent car on veut surtout relier une
    #  entrée à un résultat et pas classer

    history = model.fit(x_train, y_train, batch_size=1, epochs=2, validation_split=0.2)

    _, _, x_test, y_test = generate_training(balls, nb_hands, max_height, max_weight, seq_len, 10000)

    test_scores = model.evaluate(x_test, y_test, verbose=2)

    print("Test loss:", test_scores[0])
    print("Test accuracy:", test_scores[1])
