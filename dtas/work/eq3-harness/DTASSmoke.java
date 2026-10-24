import tas.mape.knowledge.Goal;

public class DTASSmoke {

    public static void main(String[] args) {

        Goal goal = new Goal(
            Goal.GoalType.FAILURE_RATE,
            Goal.GoalRelation.LOWER_THAN,
            0.19
        );

        System.out.println(
            "Threshold: " + goal.getValue()
        );

        System.out.println(
            "0.18 satisfies: "
            + goal.validValue(0.18)
        );

        System.out.println(
            "0.20 satisfies: "
            + goal.validValue(0.20)
        );

        System.out.println(
            "DTAS HEADLESS SMOKE: PASS"
        );
    }
}
