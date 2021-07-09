import matplotlib.pyplot as plt
from balltracker_app import *
from math import isnan

def untuplize(l, python_list=False):
    #l est une liste de tuples de même longueur.
    if len(l) == 0:
        return ()
    if not python_list:
        return tuple(np.array([elem[i] for elem in l]) for i in range(len(l[0])))
    else:
        return tuple([elem[i] for elem in l] for i in range(len(l[0])))
    
"""def tuplize(*args):
    #args est fait de listes toute de même longueur
    if len(args) == 0:
        return []
    return [tuple(arg[i] for arg in args) for i in range(len(args[0]))]"""

def threshold_intersections(threshold, x, y, interpolate=True):
    inter = []
    i_inter = []
    for i in range(len(x) - 1):
        #Vérifie si le seuil est atteint
        #Notons que y[i] est toujours strictement différent du seuil.
        if y[i] < threshold <= y[i+1] or y[i] > threshold >= y[i+1]:
            #Trouve le point d'intersection
            if interpolate:
                t_inter = (threshold * (x[i+1] - x[i]) - (x[i+1]*y[i] - x[i]*y[i+1])) / (y[i+1] - y[i])
            else:
                t_inter = x[i] 
            inter.append(t_inter)
            i_inter.append(i)
    return inter, i_inter

#ON NE GERE PAS ENCORE LES PROBLEME LIES A ABSENCE DE VALEUR !
#Problèmes acces valeurs en 0 dans init tableaux. A resoudre plus tard

def find_throws(path, ignore_nan = False, ball_name = None):
    with open(path, 'r') as f:
        data = json.load(f)
    balls = [Ball.from_dict(ball_data) for ball_data in data['balls']]
    thresholds = data['thresholds']
    thresholds[1] = -thresholds[1]
    
    #temps en ms
    to_plot = [{"x" : "t",   "y" : "x",  "xlabel" : "temps", "ylabel" : "x",  "threshold" : thresholds[0]},
               {"x" : "t",   "y" : "y",  "xlabel" : "temps", "ylabel" : "y",  "threshold" : thresholds[1]}]
               #{"x" : "tv",  "y" : "vx", "xlabel" : "temps", "ylabel" : "vx"},
               #{"x" : "tv",  "y" : "vy", "xlabel" : "temps", "ylabel" : "vy", "threshold" : 0}
               #{"x" : "ta", "y" : "ax",  "xlabel" : "temps", "ylabel" : "ax"},
               #{"x" : "ta", "y" : "ay",  "xlabel" : "temps", "ylabel" : "ay"}]
    
    fig, axes = plt.subplots(len(to_plot), 1, figsize=(12, 5*len(to_plot)))
    #figsize=(12, 5*len(to_plot))
    for ball in balls:
        if ball_name is not None and ball.name != ball_name:
            continue
        ball_data_list = [(key, *elem) for key, elem in ball.data.items()]
        ball_data_list.sort(key = lambda x : x[0])
        t, x, y = untuplize(ball_data_list)
        t_list = list(t)
        if ignore_nan:
            #On suppose x nan ssi y nan
            #Ceci est un moyen étrange mais fonctionnel de retirer les nan.
            mask = (x <= float('infinity'))
            t, x, y = t[mask], x[mask], y[mask]
        y = -y
                    
        dt = t[1:] - t[:-1]
        dt2 = dt[:-1]
        tv = t[:-1]
        ta = t[:-2]
        vx = (x[1:] - x[:-1]) / dt
        vy = (y[1:] - y[:-1]) / dt
        ax = (vx[1:] - vx[:-1]) / dt2
        ay = (vy[1:] - vy[:-1]) / dt2
        var = {"t" : t, "tv" : tv, "ta" : ta, "x" : x, "y" : y, "vx" : vx, "vy" : vy,
               "ax" : ax, "ay" : ay}
        
        ##TEST
        #Si le tracking coupe au moment ou la barre est passé... non detecté :(
        #Possible de le faire en utilisant ignore nan !
        thr_x, thr_y = thresholds
        
        x_inter, i_x_inter = threshold_intersections(thr_x, t, x)
        axes[0].scatter(x_inter, [thr_x]*len(x_inter), marker='x', color=ball.plt_color, label="Pts d'intersection")
        
        vx_inter, i_vx_inter = threshold_intersections(0, tv, vx)
        
        #Les lancers en x sont les plus simples à identifier, on ne considère que le point où le seuil
        #est traversé (et pas la durée du trajet, qui est determinée par les mouvements en y).
        i_x_throws = i_x_inter
        
        #Si jamais le premier/dernier lancé est incomplet, on ne le prend pas en compte.
        #On peut déterminer cela en examinant s'il y a un point d'intéret précédant le premier lancer en x.
        #(lancer en x = seuil franchi en x)
        #En effet, un point d'intéret est ou bien une vitesse nulle, ou bien une valeur nan,
        #indiquant respectivement que la balle vient d'être lancée, ou qu'elle était cachée au lancement,
        #mais a donc bel et bien été lancée.
        
        #On recherche les points nan.
        nan_streak = False
        i_nan = []
        for i, elem in enumerate(vx):
            if isnan(elem) and not nan_streak:
                nan_streak = True
                if i != 0:
                    i_nan.append(i-1)
            elif not isnan(elem) and nan_streak:
                nan_streak = False
                i_nan.append(i)
        
        #POI = Point Of Interest
        i_x_poi = sorted(list(set(i_vx_inter + i_nan)))
        
        #On examine si le premier lancer est complet
        if i_x_poi[0] > i_x_throws[0]:
            i_x_throws.pop(0)
        #Idem pour le dernier
        if i_x_poi[-1] < i_x_throws[-1]:
            i_x_throws.pop(-1)
        
        #On s'occupe des lancer en y.
        y_inter, i_y_inter = threshold_intersections(thr_y, t, y)
        axes[1].scatter(y_inter, [thr_y]*len(y_inter), marker='x', color=ball.plt_color, label = "Pts d'intersection")
        
        vy_inter, i_vy_inter = threshold_intersections(0, tv, vy)
        
        #On regroupe les lancers par deux pour obtenir des cloches.
        """i_bells = []
        above_threshold = y[0] > thr_y
        i_bell_start = None
        for i in range(len(y) - 1):
            new_above_threshold = y[i] > thr_y
            if not(above_threshold) and new_above_threshold:
                i_bell_start = i
            elif above_threshold and not(new_above_threshold):
                if i_bell_start is None:
                    continue
                i_bells.append((i_bell_start, i))
                i_bell_start = None    
            above_threshold = new_above_threshold
        print(f"{i_bells = }")"""
        #On regroupe les lancers par deux pour obtenir des cloches.
        #Fonctionne au vu de threshold_intersections et de stricte inégalité y_inter par rapport à thr_y
        i_bells = []
        for i in range(len(i_y_inter) - 1):
            if y[i_y_inter[i]] < thr_y and y[i_y_inter[i+1]] > thr_y:
                i_bells.append((i_y_inter[i], i_y_inter[i+1]))
        #print(f"{i_bells = }")

        #On souhaite également prendre en compte les moment où l'on perd/récupère les valeurs comme début/fin de cloche
        nan_streak = False
        i_nan = []
        for i, elem in enumerate(vy):
            if isnan(elem) and not nan_streak:
                nan_streak = True
                if i != 0:
                    i_nan.append(i-1)
            elif not isnan(elem) and nan_streak:
                nan_streak = False
                i_nan.append(i) 

        i_bell_limit_poi = sorted(list(set(i_nan + i_vy_inter)))
        #print(f"{i_bell_limit_poi = }")
        #axes[2].scatter([t[i] for i in i_bell_limit_poi], [vy[i] for i in i_bell_limit_poi], marker='x', color=ball.plt_color)
        
        #Si la première cloche arrive trop tôt, il se peut qu'on ne connaisse pas son début.
        #Dans ce cas, il faut penser à examiner précautionneusement le premier lancer en x,
        #qui peut correspondre au même lancer en y.
        #2 cas se présentent.
        #  1) La première/dernière cloche est en fait incomplète, car n'a franchie qu'une fois le seuil.
        #  2) On n'a pas de poi avant la premiere cloche/après la dernière.
        #Dans les 2 cas, il faut examiner s'il n'y a pas de lancer x associé à ces lancers y.
        #Si on ne les supprime pas, ils seraient considérés à tord comme des lancers de 1.
        """if i_bell_limit_poi[0] > i_bells[0][0]:
            i_bells.pop(0)
            i = 0
            while i < len()
        #Idem pour la dernière cloche
        if i_bell_limit_poi[-1] < i_bells[-1][1]:
            i_bells.pop(-1)"""
        i_y_inter_in_bell = [elem[0] for elem in i_bells] + [elem[1] for elem in i_bells]
        careful_x_start = None
        careful_x_end = None
        #Cas 1 - Cloche incomplète. Le cas 1 exclue le cas 2.
        if i_y_inter[0] not in i_y_inter_in_bell:
            careful_x_start = i_y_inter[0]
        if i_y_inter[-1] not in i_y_inter_in_bell:
            careful_x_end = i_y_inter[-1]
            
        #print(f"{careful_x_start = }")
        #print(f"{careful_x_end = }")
            
        #Cas 2 - Pas de POI
        if i_bells[0][0] < i_bell_limit_poi[0]:
            careful_x_start = i_bells[0][1]
            i_bells.pop(0)
        if i_bells[-1][1] > i_bell_limit_poi[-1]:
            careful_x_end = i_bells[-1][0]
            i_bells.pop(-1)
        
        #print(f"{i_x_throws = }")
        #print(f"{careful_x_start = }")
        #print(f"{careful_x_end = }")
        
        #On cherche les poi jusqu'auxquels on doit faire attention :
        if careful_x_start is not None:
            i = 0
            while i < len(i_bell_limit_poi) and i_bell_limit_poi[i] <= careful_x_start:
                i += 1
            if i == len(i_bell_limit_poi):
                critical_i = float('inf')
            else:
                critical_i = i_bell_limit_poi[i]
            #Puis on supprime les lancers de x problématiques :
            i = 0
            while i < len(i_x_throws) and i_x_throws[i] < critical_i:
                i += 1
            del i_x_throws[:i]
        #idem pour la fin:
        if careful_x_end is not None:
            i = 0
            while i < len(i_bell_limit_poi) and i_bell_limit_poi[len(i_bell_limit_poi)-i-1] >= careful_x_end:
                i += 1
            if i == len(i_bell_limit_poi):
                critical_i = -float('inf')
            else:
                critical_i = i_bell_limit_poi[len(i_bell_limit_poi)-i-1]
            i = 0
            while i < len(i_x_throws) and i_x_throws[len(i_x_throws)-i-1] > critical_i:
                i += 1
            del i_x_throws[len(i_x_throws)-i:]
        
        #print(f"{i_bells = }")
        #print(f"{i_x_throws = }")
        
        #On peut à présent se pencher sur les cloches !
        #Pour chaque cloche, on cherche les temps de lancer et de réception
        i_y_throws = []
        i_throw_start = None
        i_poi = 0 #poi = point of interest
        for i_bell_start, i_bell_end in i_bells:
            #Début de la courbe
            while i_poi < len(i_bell_limit_poi) and i_bell_limit_poi[i_poi] < i_bell_start:
                i_poi += 1
            if i_poi == len(i_bell_limit_poi):
                break
            #on est assuré que i_poi>1 car on a supprimé la première cloche sinon
            i_throw_start = i_bell_limit_poi[i_poi - 1]
            #Fin de la courbe
            while i_poi < len(i_bell_limit_poi) and i_bell_limit_poi[i_poi] < i_bell_end:
                i_poi += 1
            if i_poi == len(i_bell_limit_poi):
                break
            i_throw_end = i_bell_limit_poi[i_poi]
            #On enregistre les vols de balle pour la courbe.
            i_y_throws.append((i_throw_start, i_throw_end))
        
        #On affiche les débuts/fins de cloches.
        i_y_starts, i_y_ends = untuplize(i_y_throws, python_list=True)
        #print(f"{i_y_starts = }", f"{i_y_ends = }")
        t_starts = [t[i] for i in i_y_starts]
        t_ends = [t[i] for i in i_y_ends]
        y_starts = [y[i] for i in i_y_starts]
        y_ends = [y[i] for i in i_y_ends]
        axes[1].scatter(t_starts, y_starts, marker='^', color=ball.plt_color, label="Début cloche")
        axes[1].scatter(t_ends  , y_ends  , marker='v', color=ball.plt_color, label="Fin cloche")
            
        
        
        #On cherche quels lancers en x et en y font en fait partie du même lancer.
        #On suppose qu'un lancer en x ne peut pas passer deux fois par le seuil vertical au cours du même lancer.
        #Element de throw : (time, origin, destination, "=1") ou (time, origin, destination, ">1", length)
        #Changer de structure de donnée plus tard (namedtuple ou class à part entiere ?)
        throws = [] 
        assigned_x_throws = [False]*len(i_x_throws)
        for i_y_start, i_y_end in i_y_throws:
            throw_found = False
            for i, i_x in enumerate(i_x_throws):
                if i_y_start < i_x < i_y_end:
                    #Cas d'un lancer d'une main à l'autre de hauteur > 1
                    # Main 0 = notre gauche = main droite du jongleur
                    # Main 1 = notre droite = main gauche du jongleur
                    # On peut l'identifier comme ça grâce à la fonction threshold_intersections.
                    origin = 0 if x[i_x] < thr_x else 1
                    destination = 1 - origin
                    i_length = i_y_end - i_y_start
                    throws.append((i_y_start, origin, destination, ">1", i_length))
                    
                    #On quitte la boucle, et dit que ce lancer en x est attribué
                    throw_found = True
                    assigned_x_throws[i] = True
                    break
                    
            if not throw_found:
                #Cas d'un lancer dans la même main de hauteur > 1
                origin = 0 if x[i_y_start] < thr_x else 1
                destination = origin
                i_length = i_y_end - i_y_start
                throws.append((i_y_start, origin, destination, ">1", i_length))
                
        for i, i_x in enumerate(i_x_throws):
            if not assigned_x_throws[i]:
                #Cas d'un lancer d'une main à l'autre de hauteur = 1
                origin = 0 if x[i_x] < thr_x else 1
                destination = 1 - origin
                throws.append((i_x, origin, destination, "=1"))
        
        throws.sort(key = lambda x : x[0])
        #print(f"{throws = }")
                
        axes[0].plot(t, x, color=ball.plt_color, label='Pos $x$ balle Bleue')
        axes[1].plot(t, y, color=ball.plt_color, label='Pos $y$ balle Bleue')
        #for i, data in enumerate(to_plot):
            #axes[i].plot(var[data['x']], var[data['y']], color=ball.plt_color, label=ball.name)
        #ax[0].plot(t, x, color=ball.plt_color, label=ball.name)
        #plt.figlegend()
        
    for i, data in enumerate(to_plot): #DOUBLE UTILISATION DE DATA A CORRIFER ?
        if 'xlabel' in data:
            axes[i].set_xlabel(data['xlabel'])
        if 'ylabel' in data:
            axes[i].set_xlabel(data['ylabel'])
        #axes[i].set_xticks(data.get('xticks', np.linspace(t[0], t[-1], 5))) #a corriger
        if 'threshold' in data:
            axes[i].plot(axes[i].get_xlim(), [data['threshold']]*2, linestyle='--', label='Seuil')
    #A CONFIGURER ABSOLUMENT sinon la figure met des années à s'afficher
    #ax[0].set_xticks(np.linspace(int(t[0]), t[-1], 5))
    axes[0].set_xticks([0, 2000, 4000, 6000, 8000, 10000])
    axes[0].set_xlabel("Temps $t$ (ms)")
    axes[0].set_ylabel("$x$")
    axes[1].set_xticks([0, 2000, 4000, 6000, 8000, 10000])
    axes[1].set_xlabel("Temps $t$ (ms)")
    axes[1].set_ylabel("$y$")
    axes[0].legend(loc="lower right")
    axes[1].legend(loc="lower right")

    throws.sort(key = lambda x : x[0])
    return throws
    
    
def show_all_curves(path, ignore_nan = False):
    with open(path, 'r') as f:
        data = json.load(f)
    balls = [Ball.from_dict(ball_data) for ball_data in data['balls']]
    thresholds = data['thresholds']
    thresholds[1] = -thresholds[1]
    
    #temps en ms
    to_plot = [{"x" : "t",   "y" : "x",  "xlabel" : "temps", "ylabel" : "x",  "threshold" : thresholds[0]},
               {"x" : "t",   "y" : "y",  "xlabel" : "temps", "ylabel" : "y",  "threshold" : thresholds[1]}]
               #{"x" : "tv",  "y" : "vx", "xlabel" : "temps", "ylabel" : "vx"},
               #{"x" : "tv",  "y" : "vy", "xlabel" : "temps", "ylabel" : "vy", "threshold" : 0}]
               #{"x" : "ta", "y" : "ax",  "xlabel" : "temps", "ylabel" : "ax"},
               #{"x" : "ta", "y" : "ay",  "xlabel" : "temps", "ylabel" : "ay"}]
    
    fig, axes = plt.subplots(len(to_plot), 1, figsize=(12, 5*len(to_plot)))
    #figsize=(12, 5*len(to_plot))
    for ball in balls:
        ball_data_list = [(key, *elem) for key, elem in ball.data.items()]
        ball_data_list.sort(key = lambda x : x[0])
        t, x, y = untuplize(ball_data_list)
        t_list = list(t)
        if ignore_nan:
            #On suppose x nan ssi y nan
            #Ceci est un moyen étrange mais fonctionnel de retirer les nan.
            mask = (x <= float('infinity'))
            t, x, y = t[mask], x[mask], y[mask]
        y = -y
                    
        dt = t[1:] - t[:-1]
        dt2 = dt[:-1]
        tv = t[:-1]
        ta = t[:-2]
        vx = (x[1:] - x[:-1]) / dt
        vy = (y[1:] - y[:-1]) / dt
        ax = (vx[1:] - vx[:-1]) / dt2
        ay = (vy[1:] - vy[:-1]) / dt2
        var = {"t" : t, "tv" : tv, "ta" : ta, "x" : x, "y" : y, "vx" : vx, "vy" : vy,
               "ax" : ax, "ay" : ay}
            
        for i, data in enumerate(to_plot):
            if i==0:
                axes[i].plot(var[data['x']], var[data['y']], color=ball.plt_color, label=ball.name)
            else:
                axes[i].plot(var[data['x']], var[data['y']], color=ball.plt_color)
        #ax[0].plot(t, x, color=ball.plt_color, label=ball.name)
        #plt.figlegend()
        
    for i, data in enumerate(to_plot): #DOUBLE UTILISATION DE DATA A CORRIFER ?
        if 'xlabel' in data:
            axes[i].set_xlabel(data['xlabel'])
        if 'ylabel' in data:
            axes[i].set_xlabel(data['ylabel'])
    axes[0].set_xticks([0, 2000, 4000, 6000, 8000, 10000])
    axes[0].set_xlabel("Temps $t$ (ms)")
    axes[0].set_ylabel("$x(t)$")
    axes[1].set_xticks([0, 2000, 4000, 6000, 8000, 10000])
    axes[1].set_xlabel("Temps $t$ (ms)")
    axes[1].set_ylabel("$y(t)$")
    axes[0].legend(loc="upper right")
