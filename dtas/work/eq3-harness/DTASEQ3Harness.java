import java.io.File;
import java.io.PrintWriter;
import java.lang.reflect.Constructor;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import javafx.util.Pair;

import service.atomic.AtomicService;
import service.atomic.ServiceProfile;
import service.auxiliary.Description;
import service.auxiliary.ServiceDescription;

import tas.data.inputprofile.InputProfile;
import tas.data.inputprofile.InputProfileDataHandler;
import tas.data.inputprofile.InputProfileExecutor;
import tas.data.serviceinfo.GlobalServiceInfo;

import tas.mape.planner.ServiceCombination;
import tas.mape.probes.SystemRunProbe;

import tas.system.entity.MAPEKSystemEntity;
import tas.system.entity.MAPEKSystemEntityLoader;

import tas.workflowAnalyzer.WorkflowAnalyzer;


public class DTASEQ3Harness {

    private static final double THRESHOLD = 0.19;

    public static void main(String[] args)
        throws Exception {

        if (args.length != 3) {
            System.err.println(
                "Usage: DTASEQ3Harness "
                + "<dTAS-root> <run-id> <output.csv>"
            );
            System.exit(1);
        }

        File root = new File(args[0]);
        String runId = args[1];
        File outputFile = new File(args[2]);

        File serviceData = new File(
            root,
            "TAS_gui/resources/files/"
            + "serviceData/DefaultServiceData.xml"
        );

        File entityFile = new File(
            root,
            "TAS_gui/resources/files/entities/"
            + "System Entity 1.xml"
        );

        File profileFile = new File(
            root,
            "TAS_gui/resources/files/profiles/"
            + "SingleEntityRunNoProtocol.xml"
        );

        /*
         * Load original dTAS service environment.
         */

        GlobalServiceInfo.loadData(
            serviceData
        );

        /*
         * Reproduce the original GUI service-profile
         * initialisation.
         */

        for (
            AtomicService service :
            GlobalServiceInfo.getServices()
        ) {

            List<String> availableProfiles =
                new ArrayList<>();

            for (
                ServiceProfile existing :
                service.getServiceProfiles()
            ) {
                availableProfiles.add(
                    existing.getClass().getName()
                );
            }

            for (
                Class<?> profileClass :
                GlobalServiceInfo
                    .getServiceProfileClasses()
            ) {

                if (
                    availableProfiles.contains(
                        profileClass.getName()
                    )
                ) {
                    continue;
                }

                ServiceProfile profile = null;

                for (
                    Constructor<?> constructor :
                    profileClass.getConstructors()
                ) {

                    Class<?>[] parameterTypes =
                        constructor.getParameterTypes();

                    if (
                        parameterTypes.length == 0
                    ) {
                        profile =
                            (ServiceProfile)
                            constructor.newInstance();
                        break;
                    }

                    if (
                        parameterTypes.length == 1
                        && parameterTypes[0].equals(
                            ServiceDescription.class
                        )
                    ) {
                        profile =
                            (ServiceProfile)
                            constructor.newInstance(
                                service
                                    .getServiceDescription()
                            );
                        break;
                    }
                }

                if (profile == null) {
                    throw new IllegalStateException(
                        "Could not instantiate "
                        + profileClass.getName()
                    );
                }

                if (profile.getDefaultEnabled()) {
                    service.addServiceProfile(
                        profile
                    );
                }
            }
        }

        /*
         * Load entity and original profile.
         */

        MAPEKSystemEntity entity =
            MAPEKSystemEntityLoader.loadFromXml(
                entityFile
            );

        if (entity == null) {
            throw new IllegalStateException(
                "Entity could not be loaded."
            );
        }

        InputProfile profile =
            InputProfileDataHandler.readFromXml(
                profileFile.getPath()
            );

        if (profile == null) {
            throw new IllegalStateException(
                "Profile could not be loaded."
            );
        }

        InputProfileDataHandler.activeProfile =
            profile;

        /*
         * Reproduce ApplicationController.analyzeEntity().
         */

        WorkflowAnalyzer.analyzeWorkflow(
            entity
                .getManagedSystem()
                .getAssistanceService()
        );

        Map<
            Description,
            Pair<
                List<ServiceDescription>,
                Double
            >
        > usableServices =
            WorkflowAnalyzer
                .getUsableServicesAndChance();

        if (usableServices == null) {
            throw new IllegalStateException(
                "Workflow analysis returned "
                + "no usable services."
            );
        }

        entity
            .getManagingSystem()
            .getMonitor()
            .resetProbes();

        entity
            .getManagingSystem()
            .getKnowledge()
            .setWorkflowServiceTree(
                WorkflowAnalyzer
                    .getWorkflowServiceTree()
            );

        entity
            .getManagingSystem()
            .getKnowledge()
            .setUsedServicesAndChances(
                usableServices
            );

        /*
         * Connect original dTAS result probe.
         */

        SystemRunProbe probe =
            new SystemRunProbe();

        probe.connect(entity);

        /*
         * Execute original dTAS profile.
         */

        List<MAPEKSystemEntity> entities =
            new ArrayList<>();

        entities.add(entity);

        InputProfileExecutor.setProtocol(
            profile
        );

        InputProfileExecutor.execute(
            entities
        );

        /*
         * Extract observations.
         */

        String entityName =
            entity.getEntityName();

        List<Pair<Double, Double>> data =
            probe
                .getDataPoints()
                .get(entityName);

        List<ServiceCombination> combinations =
            probe
                .getChosenCombinations()
                .get(entityName);

        List<Integer> cycles =
            probe
                .getSystemCycles()
                .get(entityName);

        if (
            data == null
            || combinations == null
            || cycles == null
        ) {
            throw new IllegalStateException(
                "Probe returned incomplete data."
            );
        }

        if (
            data.size() != combinations.size()
            || data.size() != cycles.size()
        ) {
            throw new IllegalStateException(
                "Probe result lengths differ."
            );
        }

        /*
         * Write experimental observations.
         */

        File parent =
            outputFile.getParentFile();

        if (parent != null) {
            parent.mkdirs();
        }

        PrintWriter out =
            new PrintWriter(
                outputFile,
                "UTF-8"
            );

        out.println(
            "run_id,"
            + "cycle,"
            + "real_failure_rate,"
            + "represented_failure_rate,"
            + "absolute_error,"
            + "threshold,"
            + "real_goal_state,"
            + "represented_goal_state,"
            + "orr_preserved,"
            + "violation_type"
        );

        int violations = 0;
        int missedViolations = 0;
        int falseViolations = 0;

        for (
            int i = 0;
            i < data.size();
            i++
        ) {

            double realFailure =
                data.get(i).getKey();

            Object representedObject =
                combinations
                    .get(i)
                    .getProperty(
                        "FailureRate"
                    );

            if (
                !(representedObject
                    instanceof Number)
            ) {
                out.close();

                throw new IllegalStateException(
                    "Missing represented "
                    + "FailureRate at cycle "
                    + cycles.get(i)
                );
            }

            double representedFailure =
                ((Number) representedObject)
                    .doubleValue();

            double absoluteError =
                Math.abs(
                    realFailure
                    - representedFailure
                );

            boolean realSatisfied =
                realFailure < THRESHOLD;

            boolean representedSatisfied =
                representedFailure < THRESHOLD;

            boolean preserved =
                realSatisfied
                == representedSatisfied;

            String violationType =
                "NONE";

            if (!preserved) {

                violations++;

                if (
                    !realSatisfied
                    && representedSatisfied
                ) {
                    violationType =
                        "MISSED_VIOLATION";
                    missedViolations++;
                }
                else if (
                    realSatisfied
                    && !representedSatisfied
                ) {
                    violationType =
                        "FALSE_VIOLATION";
                    falseViolations++;
                }
            }

            out.println(
                runId
                + ","
                + cycles.get(i)
                + ","
                + realFailure
                + ","
                + representedFailure
                + ","
                + absoluteError
                + ","
                + THRESHOLD
                + ","
                + (
                    realSatisfied
                    ? "SATISFIED"
                    : "VIOLATED"
                )
                + ","
                + (
                    representedSatisfied
                    ? "SATISFIED"
                    : "VIOLATED"
                )
                + ","
                + preserved
                + ","
                + violationType
            );
        }

        out.close();

        System.out.println(
            "Run ID: " + runId
        );

        System.out.println(
            "Cycles observed: "
            + data.size()
        );

        System.out.println(
            "ORR violations: "
            + violations
        );

        System.out.println(
            "Missed violations: "
            + missedViolations
        );

        System.out.println(
            "False violations: "
            + falseViolations
        );

        System.out.println(
            "Output: "
            + outputFile.getCanonicalPath()
        );

        System.out.println(
            "DTAS EQ3 RUN: PASS"
        );

        System.exit(0);
    }
}
