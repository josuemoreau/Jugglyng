open Mlpost
open Box
open Command
open Point
open Num
open Path
open Helpers

let dot ~color ~name =
  Box.pic ~name
    (Path.fill ~color (Path.scale (Num.cm 0.3) fullcircle))

let bdot = dot ~color:Color.black

let rec foldi_desc f n b =
  if n = 0 then b
  else f n (foldi_desc f b (n - 1))

let rec foldi_asc f b n =
  if n = 0 then b
  else foldi_asc f (f b n) (n - 1)

let vd x = vec (dir x)

let emp_head_kind = Arrow.add_line Arrow.empty

let rec simple_juggling_seq_arcs dots max_time hpadding ?(juggle_forever=false) l =
  let t = ref (-1) in
  let diff = xpart (Box.ctr (Box.get "bdot_1" dots)) /. (cm 1.) -.
             xpart (Box.ctr (Box.get "bdot_0" dots)) /. (cm 1.) in
  let command_list = List.fold_left (fun acc h ->
      incr t;
      if !t < max_time then
        Arrow.point_to_point
          ~ind:(vd (-90.0))
          ~outd:(vd 90.0)
          ~sep:0.0
          ~style:jCurve
          ~kind:emp_head_kind
          (Box.ctr (Box.get ("bdot_" ^ string_of_int !t) dots))
          (if !t + h < max_time then
             (Box.ctr
                (Box.get ("bdot_" ^ (string_of_int (!t + h))) dots))
           else
             (Point.shift
                (Box.ctr (Box.get ("bdot_" ^ (string_of_int (max_time - 1))) dots))
                (cmp (diff *. float_of_int (!t + h - max_time + 1), 0.0)))
          ) :: acc
      else acc
    ) [] l in
  let t' = ref 0 in
  let before = List.fold_left (fun acc h ->
      decr t';
      Arrow.point_to_point
        ~ind:(vd (-90.0))
        ~outd:(vd 90.0)
        ~sep:0.0
        ~style:jCurve
        ~kind:emp_head_kind
        (Point.shift
           (Box.ctr (Box.get "bdot_0" dots))
           (cmp (diff *. float_of_int !t', 0.0)))
        (Point.shift
           (Box.ctr (Box.get "bdot_0" dots))
           (cmp (diff *. float_of_int (!t' + h), 0.0)))
      :: acc
    ) [] (List.rev l) in
  let pic = seq (command_list @ if juggle_forever then before else []) in
  let height = ypart (Picture.north pic) /. (cm 1.) in
  let width =
    xpart
      (Box.ctr (Box.get ("bdot_" ^ (string_of_int (max_time - 1))) dots))
    /. (cm 1.) +. hpadding
  in
  Picture.clip
    pic
    (Path.path
       ~style:jLine
       ~cycle:jLine
       ~scale:cm
       [(-. diff /. 2., 0.); (width, 0.);
        (width, height); (-. diff /. 2., height)])

let simple_juggling_seq max_time hpadding l
    ?(juggle_forever=false) ~show_time ~show_height under_l =
  let dots = Box.tabularl ~vpadding:(cm 0.10) ~hpadding:(cm hpadding) ([
      foldi_asc (fun l i ->
          bdot ("bdot_" ^ string_of_int (i - 1)) :: l) [] max_time]
      @ (if show_height then [foldi_asc (fun acc i ->
          Box.tex (string_of_int (List.nth l (i - 1))) :: acc) [] max_time]
         else [])
      @ (if show_time then [foldi_asc (fun acc i ->
          Box.tex (string_of_int (i - 1)) :: acc) [] max_time]
         else [])
      @ (if under_l <> [] then [List.map (fun s -> Box.tex s) under_l] else [])) in
  seq ([
      Box.draw dots;
      simple_juggling_seq_arcs dots max_time hpadding l ~juggle_forever
    ])

let rec multiplex_juggling_seq_arcs dots max_time hpadding ?(juggle_forever=false) l special_seq =
  let t = ref (-1) in
  let diff = xpart (Box.ctr (Box.get "bdot_1" dots)) /. (cm 1.) -.
             xpart (Box.ctr (Box.get "bdot_0" dots)) /. (cm 1.) in
  let command_list = List.fold_left (fun acc hlist ->
      incr t;
      List.fold_left (fun acc h ->
          if !t < max_time then
            Arrow.point_to_point
              ~ind:(vd (-90.0))
              ~outd:(vd 90.0)
              ~sep:0.0
              ~style:jCurve
              ~kind:emp_head_kind
              (Box.ctr (Box.get ("bdot_" ^ string_of_int !t) dots))
              (if !t + h < max_time then
                 (Box.ctr
                    (Box.get ("bdot_" ^ (string_of_int (!t + h))) dots))
               else
                 (Point.shift
                    (Box.ctr (Box.get ("bdot_" ^ (string_of_int (max_time - 1))) dots))
                    (cmp (diff *. float_of_int (!t + h - max_time + 1), 0.0)))
              ) :: acc
          else acc
        ) acc hlist
    ) [] l in
  let t' = ref 0 in
  let before = List.fold_left (fun acc hlist ->
      decr t';
      List.fold_left (fun acc h ->
          Arrow.point_to_point
            ~ind:(vd (-90.0))
            ~outd:(vd 90.0)
            ~sep:0.0
            ~style:jCurve
            ~kind:emp_head_kind
            (Point.shift
               (Box.ctr (Box.get "bdot_0" dots))
               (cmp (diff *. float_of_int !t', 0.0)))
            (Point.shift
               (Box.ctr (Box.get "bdot_0" dots))
               (cmp (diff *. float_of_int (!t' + h), 0.0)))
          :: acc
        ) acc hlist
    ) [] (List.rev l) in
  let pic = seq (command_list @ (if juggle_forever then before else []) @ special_seq) in
  let height = ypart (Picture.north pic) /. (cm 1.) in
  let width =
    xpart
      (Box.ctr (Box.get ("bdot_" ^ (string_of_int (max_time - 1))) dots))
    /. (cm 1.) +. hpadding
  in
  Picture.clip
    pic
    (Path.path
       ~style:jLine
       ~cycle:jLine
       ~scale:cm
       [(-. diff /. 2., 0.); (width, 0.);
        (width, height); (-. diff /. 2., height)])

let multiplex_juggling_seq max_time hpadding ?(juggle_forever=false) l =
  let dots = Box.tabularl ~vpadding:(cm 0.10) ~hpadding:(cm hpadding) ([
      foldi_asc (fun l i ->
          bdot ("bdot_" ^ string_of_int (i - 1)) :: l) [] max_time]) in
  seq ([
      Box.draw dots;
      multiplex_juggling_seq_arcs dots max_time hpadding l [] ~juggle_forever;
    ])

let multiplex_juggling_seq1 max_time hpadding ?(juggle_forever=false) l =
  let dots = Box.tabularl ~vpadding:(cm 0.10) ~hpadding:(cm hpadding) ([
      foldi_asc (fun l i ->
          bdot ("bdot_" ^ string_of_int (i - 1)) :: l) [] max_time]) in
  let diff = xpart (Box.ctr (Box.get "bdot_1" dots)) /. (cm 1.) -.
             xpart (Box.ctr (Box.get "bdot_0" dots)) /. (cm 1.) in
  let special_seq = [
    Arrow.point_to_point
      ~ind:(vd (-60.0))
      ~outd:(vd 60.0)
      ~sep:0.0
      ~style:jCurve
      ~kind:emp_head_kind
      (Box.ctr (Box.get "bdot_0" dots))
      (Box.ctr (Box.get "bdot_1" dots));
    Arrow.point_to_point
      ~ind:(vd (-60.0))
      ~outd:(vd 60.0)
      ~sep:0.0
      ~style:jCurve
      ~kind:emp_head_kind
      (Box.ctr (Box.get "bdot_2" dots))
      (Box.ctr (Box.get "bdot_3" dots));
    Arrow.point_to_point
      ~ind:(vd (-60.0))
      ~outd:(vd 60.0)
      ~sep:0.0
      ~style:jCurve
      ~kind:emp_head_kind
      (Box.ctr (Box.get "bdot_3" dots))
      (Box.ctr (Box.get "bdot_4" dots));
    Arrow.point_to_point
      ~ind:(vd (-60.0))
      ~outd:(vd 60.0)
      ~sep:0.0
      ~style:jCurve
      ~kind:emp_head_kind
      (Box.ctr (Box.get "bdot_5" dots))
      (Box.ctr (Box.get "bdot_6" dots));
    Arrow.point_to_point
      ~ind:(vd (-60.0))
      ~outd:(vd 60.0)
      ~sep:0.0
      ~style:jCurve
      ~kind:emp_head_kind
      (Point.shift
         (Box.ctr (Box.get "bdot_0" dots))
         (cmp (diff *. -1.0, 0.0)))
      (Box.ctr (Box.get "bdot_0" dots));
    Arrow.point_to_point
      ~ind:(vd (-60.0))
      ~outd:(vd 60.0)
      ~sep:0.0
      ~style:jCurve
      ~kind:emp_head_kind
      (Box.ctr (Box.get "bdot_6" dots))
      (Point.shift
         (Box.ctr (Box.get "bdot_6" dots))
         (cmp (diff, 0.0)))
  ] in
  seq ([
      Box.draw dots;
      multiplex_juggling_seq_arcs dots max_time hpadding l special_seq ~juggle_forever
    ])

let rec multihand_juggling_seq_arcs dots max_time hpadding ?(juggle_forever=false) l =
  let m = ref (-1) in
  let diff = xpart (Box.ctr (Box.get "bdot_0_1" dots)) /. (cm 1.) -.
             xpart (Box.ctr (Box.get "bdot_0_0" dots)) /. (cm 1.) in
  let command_list =
    List.fold_left (fun acc hand_throws ->
        let t = ref (-1) in
        incr m;
        List.fold_left (fun acc throws ->
            incr t;
            List.fold_left (fun acc (h, d) ->
                if !t < max_time then begin
                  Arrow.point_to_point
                    ?ind:(if !m = d then Some (vd (-90.0)) else None)
                    ?outd:(if !m = d then Some (vd 90.0) else None)
                    ~sep:0.0
                    ~style:jCurve
                    ~kind:emp_head_kind
                    (Box.ctr (Box.get ("bdot_" ^ string_of_int !m ^ "_" ^ string_of_int !t) dots))
                    (if !t + h < max_time then
                       (Box.ctr
                          (Box.get ("bdot_" ^ string_of_int d ^ "_" ^ (string_of_int (!t + h))) dots))
                     else
                       (Point.shift
                          (Box.ctr (Box.get ("bdot_" ^ string_of_int d ^ "_" ^ (string_of_int (max_time - 1))) dots))
                          (cmp (diff *. float_of_int (!t + h - max_time + 1), 0.0)))
                    ) :: acc
                end else acc
              ) acc throws
          ) acc hand_throws
      ) [] l in
  m := -1;
  let before =
    List.fold_left (fun acc hand_throws ->
        let t' = ref 0 in
        incr m;
        List.fold_left (fun acc throws ->
            decr t';
            List.fold_left (fun acc (h, d) ->
                Arrow.point_to_point
                  ?ind:(if !m = d then Some (vd (-90.0)) else None)
                  ?outd:(if !m = d then Some (vd 90.0) else None)
                  ~sep:0.0
                  ~style:jCurve
                  ~kind:emp_head_kind
                  (Point.shift
                     (Box.ctr (Box.get ("bdot_" ^ string_of_int !m ^ "_0") dots))
                     (cmp (diff *. float_of_int !t', 0.0)))
                  (Point.shift
                     (Box.ctr (Box.get ("bdot_" ^ string_of_int d ^ "_0") dots))
                     (cmp (diff *. float_of_int (!t' + h), 0.0)))
                :: acc
              ) acc throws
          ) acc (List.rev hand_throws)
      ) [] l in
  let pic = seq (command_list @ if juggle_forever then before else []) in
  let south = ypart (Picture.south pic) /. (cm 1.) in
  let north = ypart (Picture.north pic) /. (cm 1.) in
  let width =
    xpart
      (Box.ctr (Box.get ("bdot_0_" ^ (string_of_int (max_time - 1))) dots))
    /. (cm 1.) +. hpadding
  in
  Picture.clip
    pic
    (Path.path
       ~style:jLine
       ~cycle:jLine
       ~scale:cm
       [(-. diff /. 2., south); (width, south);
        (width, north); (-. diff /. 2., north)])

let multihand_juggling_seq nb_hands max_time hpadding vpadding
    ?(juggle_forever=false) l =
  let dots = Box.tabularl ~vpadding:(cm vpadding) ~hpadding:(cm hpadding) (
      foldi_asc (fun acc h ->
          (foldi_asc (fun l i ->
               bdot ("bdot_" ^ string_of_int (h - 1)
                     ^ "_" ^ string_of_int (i - 1)) :: l) [] max_time) :: acc)
        [] nb_hands
    ) in
  seq ([
      Box.draw dots;
      multihand_juggling_seq_arcs dots max_time hpadding l ~juggle_forever
    ])

let fig0 =
  (simple_juggling_seq 10 0.7 [3; 3; 3; 3; 3; 3; 3; 3; 3; 3] [] ~show_time:true
     ~show_height:false)

let fig1 =
  simple_juggling_seq 10 0.7 [4; 2; 0; 4; 2; 0; 4; 2; 0; 4] [] ~show_time:true
    ~show_height:false

let fig2 =
  simple_juggling_seq 4 0.5 [3; 1; 0; 0] ["do"; "ré"; "do"; "ré"] ~show_time:true
    ~show_height:false

let fig3 =
  simple_juggling_seq 4 0.5 [2; 2; 0; 0] ["ré"; "do"; "do"; "ré"] ~show_time:true
    ~show_height:false

let fig4 =
  let tex = Box.tex ~style:Box.Circle ~stroke:(Some Color.black) ~dx:(cm 0.2) in
  let f = Box.vbox ~padding:(cm 0.1) [
      tex "1";
      tex "2"
    ] in
  seq [ Box.draw f ]

let fig5 =
  let tex = Box.tex ~style:Box.Circle ~stroke:(Some Color.black) ~dx:(cm 0.2) in
  let f = Box.vbox ~padding:(cm 0.1) [
      Box.hbox ~padding:(cm 0.1) [
        tex "3"; tex "1"
      ];
      tex "2"
    ] in
  seq [ Box.draw f ]

let fig6 =
  let tex = Box.tex ~style:Box.Circle ~stroke:(Some Color.black) ~dx:(cm 0.2) in
  let f = Box.vbox ~padding:(cm 0.1) [
      Box.hbox ~padding:(cm 0.1) [
        tex ~fill:(Color.gray 0.9) "3"; tex ~fill:(Color.gray 0.9) "1"
      ];
      tex ~fill:(Color.gray 0.9) "2"
    ] in
  let f4 = Box.shift (cmp (0.35, -0.25)) (tex ~fill:Color.white "4") in
  seq [ Box.draw f; Box.draw f4 ]

let fig_do_re_mi =
  let l = Box.same_size [Box.tex "do"; Box.tex "ré"; Box.tex "mi"] in
  let c = Box.box ~style:Box.Circle ~stroke:(Some Color.black) ~dx:(cm 0.2) in
  let f = Box.vbox ~padding:(cm 0.1) [
      Box.hbox ~padding:(cm 0.1) ~same_width:true [
        c (List.nth l 0); c (List.nth l 1)
      ];
      c (List.nth l 2)
    ] in
  ("do_re_mi", seq [ Box.draw f ])

let fig_re_do_mi =
  let l = Box.same_size [Box.tex "do"; Box.tex "ré"; Box.tex "mi"] in
  let c = Box.box ~style:Box.Circle ~stroke:(Some Color.black) ~dx:(cm 0.2) in
  let f = Box.vbox ~padding:(cm 0.1) [
      Box.hbox ~padding:(cm 0.1) ~same_width:true [
        c (List.nth l 1); c (List.nth l 0)
      ];
      c (List.nth l 2)
    ] in
  ("re_do_mi", seq [ Box.draw f ])

let fig_3_1_2 =
  ("3_1_2", simple_juggling_seq 10 0.7 [3; 1; 2; 3; 1; 2; 3; 1; 2; 3; 1; 2] []
     ~show_time:false ~show_height:true ?juggle_forever:(Some true))

let fig_2_3_2 =
  ("2_3_2", simple_juggling_seq 5 0.7 [2; 3; 2; 0; 0; 0; 0; 0] ["2"; "3"; "2"; ""; ""]
     ~show_time:false ~show_height:false)

let fig_3_0_3_0 =
  ("3_0_3_0", simple_juggling_seq 4 0.7 [3; 0; 3; 0; 0; 0; 0; 0] ["3"; "0"; "3"; "0"]
     ~show_time:false ~show_height:false)

let fig_13_2_0 =
  ("13_2_0", multiplex_juggling_seq 7 0.7
     [[1; 3]; [2]; [0]; [1; 3]; [2]; [0]; [1; 3]; [2]; [0]]
     ~juggle_forever:true)

(*
   2_0         & 2_1 & 1_2
   1_0 2_2     & 2_0 & 0
   [1 3]_1 3_2 & 0   & 1_2
*)

let fig_multihand =
  ("multihand", multihand_juggling_seq 3 7 0.7 1.5
     [
       [                [(2, 0)]; [(2, 1)]; [(1, 2)];
                        [(2, 0)]; [(2, 1)]; [(1, 2)];
                        [(2, 0)]; [(2, 1)]; [(1, 2)]];
       [        [(1, 0); (2, 2)]; [(2, 0)];       [];
                [(1, 0); (2, 2)]; [(2, 0)];       [];
                [(1, 0); (2, 2)]; [(2, 0)];       []];
       [[(1, 1); (3, 1); (3, 2)];       []; [(1, 2)];
        [(1, 1); (3, 1); (3, 2)];       []; [(1, 2)];
        [(1, 1); (3, 1); (3, 2)];       []; [(1, 2)]]
     ] ~juggle_forever:true)

let fig_aplatissement =
  ("aplatissement", multiplex_juggling_seq1 7 0.7
     [[2; 1; 2; 1; 3; 3]; [2; 2]; [1; 1]; [2; 1; 2; 1; 3; 3]; [2; 2]; [1; 1];
      [2; 1; 2; 1; 3; 3]; [2; 2]; [1; 1]]
     ~juggle_forever:true)

let draw_line a b =
  Path.draw (Path.path ~scale:cm [a; b])

let draw_bdot p =
  Box.draw (Box.shift (cmp p) (bdot ""))

module StringMap = Map.Make(String)

let pre_traitement_fig hpadding vpadding ?(show_decomp=true) ?(throws=false) musique =
  let map = List.fold_right (fun (t, n) acc ->
      try
        StringMap.add n (t :: StringMap.find n acc) acc
      with _ ->
        StringMap.add n [t] acc
    ) musique StringMap.empty in
  let max_time, last_note =
    List.fold_left (fun (max_t, max_n) (t, n) ->
        if t > max_t then (t, n) else (max_t, max_n)
      ) (List.hd musique) musique in
  let min_time, first_note =
    List.fold_left (fun (min_t, min_n) (t, n) ->
        if t < min_t then (t, n) else (min_t, min_n)
      ) (List.hd musique) musique in
  let musique_timeline = Array.make (max_time + 1) [] in
  let () = List.iter (fun (t, n) -> musique_timeline.(t) <- n :: musique_timeline.(t)) musique in
  let line = ref 0 in
  let lines_htbl = Hashtbl.create 100 in
  let t = ref (max_time + 1) in
  let main_dots = Array.fold_right (fun l acc ->
      decr t;
      (if l = [] then Box.tex "" else bdot (string_of_int !t)) :: acc
    ) musique_timeline [] in
  let notes_dots = Array.fold_right (fun l acc ->
      match l with
      | []  -> Box.tex "" :: acc
      | [n] -> Box.tex n  :: acc
      | _   ->
        Box.tex
          ("[" ^
           (List.fold_left (fun acc n -> n ^ "," ^ acc) (List.hd l) (List.tl l)) ^
           "]")
        :: acc
    ) musique_timeline [] in
  let dots = Box.tabularl ~hpadding:(cm hpadding) ~vpadding:(cm vpadding) ([
      (if show_decomp then Box.tex "" :: main_dots else main_dots);
      (if show_decomp then Box.tex "" :: notes_dots else notes_dots)
    ] @ if not show_decomp then [] else List.rev (
      StringMap.fold (fun n times acc ->
          incr line;
          let a = Array.make (max_time + 1) (Box.tex ~name:(string_of_int !line) "") in
          List.iter (fun t ->
              begin try
                 let (last_t, last_n) = Hashtbl.find lines_htbl !line in
                 if t > last_t then
                   Hashtbl.replace lines_htbl !line (t, n)
                 else ()
                with _ ->
                  Hashtbl.add lines_htbl !line (t, n) end;
              a.(t) <- bdot (string_of_int t ^ "_" ^ n)) times;
          (Box.tex n :: Array.to_list a) :: acc) map [])) in
  let first_dot_x = xpart
      (Box.ctr
         (Box.get (string_of_int min_time) dots)) /. (cm 1.) in
  let last_dot_x = xpart
      (Box.ctr
         (Box.get (string_of_int max_time) dots)) /. (cm 1.) in
  let lines = if not show_decomp then [] else foldi_asc (fun acc n ->
      let y = ypart (Box.ctr (Box.get (string_of_int n) dots)) /. (cm 1.) in
      let last_t, last_n = Hashtbl.find lines_htbl n in
      let last_x =
        xpart (Box.ctr (Box.get (string_of_int last_t ^ "_" ^ last_n) dots)) /. (cm 1.) in
      draw_line (first_dot_x, y) (last_x, y) :: acc
    ) [] !line in
  seq ([
      Box.draw dots;
      draw_line (first_dot_x, 0.) (last_dot_x, 0.);
    ] @ lines)

let fig_pre_traitement_timeline =
  ("pre_traitement_timeline",
   pre_traitement_fig 0.7 0.3 [
     (0, "do"); (1, "do"); (2, "do"); (3, "ré"); (4, "mi"); (6, "ré"); (8, "do");
     (9, "mi"); (10, "ré"); (11, "ré"); (12, "do")
   ] ~show_decomp:false)

let fig_pre_traitement =
  ("pre_traitement",
   pre_traitement_fig 0.7 0.3 [
     (0, "do"); (1, "do"); (2, "do"); (3, "ré"); (4, "mi"); (6, "ré"); (8, "do");
     (9, "mi"); (10, "ré"); (11, "ré"); (12, "do")
   ])

let state = Box.tex ~dx:(bp 4.)

let final = Box.box ~style:Circle

let transition states tex anchor ?outd ?ind x_name y_name =
  let x = Box.get x_name states and y = Box.get y_name states in
  let outd = match outd with None -> None | Some a -> Some (vec (dir a)) in
  let ind = match ind with None -> None | Some a -> Some (vec (dir a)) in
  Arrow.draw ~tex ~anchor (cpath ?outd ?ind x y)

let loop states tex name =
  let box = Box.get name states in
  let a = Point.shift (Box.south box) (Point.pt (cm 0., cm (-0.4))) in
  let c = Box.ctr box in
  let p = Path.pathk [
      knotp ~r: (vec (dir 225.)) c;
      knotp a;
      knotp ~l: (vec (dir 135.)) c;
    ] in
  let bp = Box.bpath box in
  Arrow.draw ~tex ~anchor:`Bot (cut_after bp (cut_before bp p))

let initial states name =
  let b = Box.get name states in
  let p = Box.west b in
  Arrow.draw (Path.pathp [ Point.shift p (Point.pt (cm (-0.3), zero)); p ])

let fig_automate =
  let emp = Box.tex "" in
  let s n = state ~name:n n in
  let states = Box.tabularl ~hpadding:(cm 1.0) ~vpadding:(cm 1.0) [
      [s "10101"; emp; s "01110"; emp; s "00111"];
      [emp; s "01011"; emp; emp; emp];
      [emp; emp; s "10110"; emp; s "10011"];
      [emp; s "01101"; emp; emp; emp];
      [s "11010"; emp; s "11100"; emp; s "11001"]
    ] in
  ("automate",
   seq [
     Box.draw states;
     transition states "1" `East "10101" "11010" ~ind:(-110.0) ~outd:(-70.0);
     transition states "3" `North "10101" "01110";
     transition states "5" `Northeast "10101" "01011";
     transition states "0" `East "01110" "11100" ~ind:147.0 ~outd:33.0;
     transition states "0" `South "00111" "01110";
     transition states "0" `Northeast "01011" "10110";
     transition states "1" `East "10110" "11100";
     transition states "4" `East "10110" "01110";
     transition states "5" `Northwest "10110" "01101";
     transition states "1" `North "10011" "10110";
     transition states "2" `Northeast "10011" "01110";
     transition states "5" `East "10011" "00111";
     transition states "0" `Northwest "01101" "11010";
     transition states "2" `North "11010" "11100";
     transition states "4" `Northwest "11010" "10110" ~ind:00.0;
     transition states "5" `West "11010" "10101" ~ind:70.0 ~outd:110.0;
     loop states "3" "11100";
     transition states "4" `South "11100" "11010" ~ind:160.0;
     transition states "5" `North "11100" "11001";
     transition states "2" `South "11001" "11010" ~ind:140.0;
     transition states "3" `Northeast "11001" "10110";
     transition states "5" `East "11001" "10011"
   ])

let fig_automate_musical =
  let s n = state ~name:n n in
  let matrix x = "$\\begin{array}{cccc} " ^ x ^ " \\end{array}$" in
  let s1 = matrix "\\{$do$\\} & \\emptyset & \\emptyset & \\emptyset \\\\ \\emptyset & \\{$ré$\\} & \\emptyset & \\emptyset" in
  let s2 = matrix "\\{$do$\\} & \\emptyset & \\emptyset & \\emptyset \\\\ \\{$ré$\\} & \\emptyset & \\emptyset & \\emptyset" in
  let s3 = matrix "\\emptyset & \\emptyset & \\emptyset & \\emptyset \\\\ \\{$do, ré$\\} & \\emptyset & \\emptyset & \\emptyset" in
  let s4 = matrix "\\emptyset & \\{$do$\\} & \\emptyset & \\emptyset \\\\ \\{$ré$\\} & \\emptyset & \\emptyset & \\emptyset" in
  let s5 = matrix "\\emptyset & \\emptyset & \\emptyset & \\emptyset \\\\ \\{$ré$\\} & \\emptyset & \\{$do$\\} & \\emptyset" in
  let s6 = matrix "\\emptyset & \\emptyset & \\emptyset & \\emptyset \\\\ \\{$ré$\\} & \\{$do$\\} & \\emptyset & \\emptyset" in
  let states = Box.tabularl ~hpadding:(cm 2.0) ~vpadding:(cm 3.0) [
      [s s5; s s1; s s2];
      [s s6; s s3; s s4]
    ] in
  ("automate_musical",
   seq [
     Box.draw states;
     transition states "$1_{\\textrm{do}, 0}$" `North s1 s2 ~ind:(-10.0);
     transition states "$1_{\\textrm{do}, 1}$" `East s1 s3 ~ind:(-110.0);
     transition states "$2_{\\textrm{do}, 0}$" `Northeast s1 s4 ~ind:(-50.0);
     transition states "$3_{\\textrm{do}, 1}$" `North s1 s5;
     transition states "$1_{\\textrm{do}, 0}, 2_{\\textrm{ré}, 1}$" `South s2 s1 ~ind:(170.0);
     transition states "$2_{\\textrm{do}, 0}, 1_{\\textrm{ré}, 1}$" `East s2 s4 ~ind:(-110.0);
     transition states "$1_{\\textrm{do}, 0}, 2_{\\textrm{ré}, 1}$" `West s3 s1 ~ind:(70.0);
     transition states "$2_{\\textrm{do}, 0}, 1_{\\textrm{ré}, 1}$" `South s4 s3;
     transition states "$1_{\\textrm{ré}, 1}$" `West s4 s2 ~ind:(70.0);
     transition states "$2_{\\textrm{ré}, 1}$" `South s4 s1 ~ind:(130.0);
     transition states "$1_{\\textrm{ré}, 1}$" `West s5 s6;
     transition states "$1_{\\textrm{ré}, 1}$" `South s6 s3;
   ])

let () =
  let figs : Mlpost.Command.t list = [fig0; fig1; fig2; fig3; fig4; fig5; fig6] in
  List.iteri (fun i x -> Metapost.emit ("figure-" ^ string_of_int i) x) figs;

  let figs = [
    fig_do_re_mi; fig_re_do_mi; fig_3_1_2; fig_2_3_2; fig_3_0_3_0;
    fig_13_2_0; fig_aplatissement; fig_multihand;
    fig_pre_traitement; fig_pre_traitement_timeline;
    fig_automate; fig_automate_musical
  ] in
  List.iteri (fun i (name, x) -> Metapost.emit ("figure-" ^ name) x) figs;

  Metapost.dump ~pdf:true "figs"
