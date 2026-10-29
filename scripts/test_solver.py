from core.solver import solve_for_arm, check_plan

scrambled = "DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD"

moves, actions = solve_for_arm(scrambled)

turns = actions.count("u") + actions.count("u'")
rotations = len(actions) - turns

print("kociemba:", " ".join(moves))
print("arm:     ", " ".join(actions))
print(len(moves), "moves ->", turns, "turns +", rotations, "rotations")
print("plan correct:", check_plan(moves, actions))