import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.PrintStream;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.junit.After;
import org.junit.Assert;
import org.junit.BeforeClass;
import org.junit.FixMethodOrder;
import org.junit.Ignore;
import org.junit.Test;
import org.junit.runners.MethodSorters;
import org.mitre.synthea.TestHelper;
import org.mitre.synthea.engine.Generator;
import org.mitre.synthea.helpers.Config;
import org.mitre.synthea.world.agents.PayerManager;
import org.mitre.synthea.world.geography.Location;

@FixMethodOrder(MethodSorters.NAME_ASCENDING)
public class AppTest {
  private static String testStateDefault;
  private static String testTownDefault;
  private static String testStateAlternative;
  private static String testTownAlternative;

  @BeforeClass
  public static void testSetup() throws Exception {
    TestHelper.loadTestProperties();
    testStateDefault = Config.get("test_state.default", "Massachusetts");
    testTownDefault = Config.get("test_town.default", "Bedford");
    testStateAlternative = Config.get("test_state.alternative", "Utah");
    testTownAlternative = Config.get("test_town.alternative", "Salt Lake City");
    Generator.DEFAULT_STATE = testStateDefault;
    PayerManager.clear();
    PayerManager.loadPayers(new Location(testStateDefault, testTownDefault));
  }

  /**
   * Restore Config to its base state after each test to prevent cross-test pollution.
   * Removes keys that individual tests are known to set, then reloads test.properties.
   * PayerManager is cleared — setUp() will reload default-state payers.
   */
  @After
  public void tearDown() throws Exception {
    Config.remove("test_key");
    Config.remove("exporter.fhir.export");
    Config.remove("test.bar");
    TestHelper.loadTestProperties();
    PayerManager.clear();
  }

  /**
   * Ensure PayerManager is loaded for the default location before each test.
   * Tests that need an alternative location must call PayerManager.clear() and
   * PayerManager.loadPayers() at the start of the test.
   */
  @org.junit.Before
  public void setUp() {
    PayerManager.loadPayers(new Location(testStateDefault, testTownDefault));
  }

  // ---------------------------------------------------------------------------
  // Helper methods
  // ---------------------------------------------------------------------------

  @FunctionalInterface
  private interface ThrowingRunnable {
    void run() throws Exception;
  }

  /**
   * Captures System.out during execution of the given action and returns
   * the captured output as a String. System.out is restored after execution.
   */
  private String captureSystemOut(ThrowingRunnable action) throws Exception {
    PrintStream original = System.out;
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    System.setOut(new PrintStream(out, true));
    try {
      action.run();
    } finally {
      out.flush();
      System.setOut(original);
    }
    return out.toString();
  }

  /**
   * Captures both System.out and System.err during execution of the given action
   * and returns the combined captured output. Both streams are restored after execution.
   */
  private String captureSystemOutAndErr(ThrowingRunnable action) throws Exception {
    PrintStream originalOut = System.out;
    PrintStream originalErr = System.err;
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    PrintStream capturing = new PrintStream(out, true);
    System.setOut(capturing);
    System.setErr(capturing);
    try {
      action.run();
    } finally {
      out.flush();
      System.setOut(originalOut);
      System.setErr(originalErr);
    }
    return out.toString();
  }

  private void assertOutputContains(String output, String expected) {
    Assert.assertTrue(
        "Expected output to contain \"" + expected + "\" but it did not.\nOutput:\n" + output,
        output.contains(expected));
  }

  private void assertOutputNotContains(String output, String unexpected) {
    Assert.assertFalse(
        "Expected output NOT to contain \"" + unexpected + "\" but it did.\nOutput:\n" + output,
        output.contains(unexpected));
  }

  // ---------------------------------------------------------------------------
  // Core functionality tests
  // ---------------------------------------------------------------------------

  @Test
  public void testApp() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "3", testStateDefault, testTownDefault};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Population:");
    assertOutputContains(output, "Seed:");
    assertOutputContains(output, "Location:");
    assertOutputContains(output, "alive=3");
    assertOutputContains(output, "dead=");
    String locationString = "Location: " + testTownDefault + ", " + testStateDefault;
    assertOutputContains(output, locationString);
  }

  @Test
  public void testAppWithGender() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "4", "-g", "M"};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Gender: M");
    assertOutputContains(output, "Seed:");
    assertOutputContains(output, "alive=4");
    assertOutputContains(output, "dead=");
    assertOutputNotContains(output, "y/o F");
    assertOutputContains(output, "Location: " + Generator.DEFAULT_STATE);
  }

  @Test
  public void testAppWithAges() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "3", "-a", "30-39"};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Seed:");
    assertOutputContains(output, "alive=3");
    assertOutputContains(output, "Location: " + Generator.DEFAULT_STATE);
    String regex = "(.\n)*(3[0-9] y/o)(.\n)*";
    Assert.assertTrue(
        "Expected output to contain at least one person aged 30-39",
        Pattern.compile(regex).matcher(output).find());
    regex = "(.\n)*(\\(([0-9]|[0-2][0-9]|[4-9][0-9]) y/o)(.\n)*";
    Assert.assertFalse(
        "Expected output to NOT contain people outside the 30-39 age range",
        output.matches(regex));
  }

  @Test
  public void testAppWithDifferentLocation() throws Exception {
    PayerManager.clear();
    PayerManager.loadPayers(new Location(testStateAlternative, testTownAlternative));
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "3", testStateAlternative, testTownAlternative};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Seed:");
    assertOutputContains(output, "alive=3");
    String locationString = "Location: " + testTownAlternative + ", " + testStateAlternative;
    assertOutputContains(output, locationString);
  }

  @Ignore
  @Test
  public void testAppWithOverflow() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "3", "-o", "false"};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Seed:");
    String regex = "alive=(\\d+), dead=(\\d+)";
    Matcher matches = Pattern.compile(regex).matcher(output);
    Assert.assertTrue(
        "Expected output to match alive/dead counts pattern",
        matches.find());
    int alive = Integer.parseInt(matches.group(1));
    int dead = Integer.parseInt(matches.group(2));
    Assert.assertEquals(
        String.format("Expected 3 total records, got %d alive and %d dead", alive, dead),
        3, alive + dead);
  }

  // ---------------------------------------------------------------------------
  // Module filter tests
  // ---------------------------------------------------------------------------

  @Test
  public void testAppWithModuleFilter() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "0", "-m", "copd" + File.pathSeparator + "allerg*"};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Seed:");
    assertOutputContains(output, "Modules:");
    assertOutputContains(output, "COPD Module");
    assertOutputContains(output, "Allergic");
    assertOutputContains(output, "Allergies");
    assertOutputNotContains(output, "asthma");
  }

  @Test
  public void testAppWithLocalModuleDir() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "0",
        "-d", "src/test/resources/module", "-m", "copd*"};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Seed:");
    assertOutputContains(output, "Modules:");
    assertOutputContains(output, "COPD Module");
    assertOutputContains(output, "COPD_TEST Module");
  }

  @Test
  public void testAppWithModuleFilterNoMatches() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "1", "-m", "zzz_nonexistent_module*"};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Modules:");
    assertOutputContains(output, "alive=1");
  }

  // ---------------------------------------------------------------------------
  // Config override tests
  // ---------------------------------------------------------------------------

  @Test
  public void testAppWithConfigSetting() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "0",
        "--test_key", "changed value", "--exporter.fhir.export=true"};
    App.main(args);

    Assert.assertEquals(
        "Config key should be updated via command-line argument",
        "changed value", Config.get("test_key"));
    Assert.assertEquals(
        "FHIR export config should be set to true",
        "true", Config.get("exporter.fhir.export"));
  }

  @Test
  public void testAppWithLocalConfigFile() throws Exception {
    TestHelper.exportOff();
    Config.set("test.bar", "42");
    String[] args = {"-s", "0", "-p", "0",
        "-c", "src/test/resources/test2.properties"};
    App.main(args);

    Assert.assertEquals(
        "Config should be overridden by local config file",
        "24", Config.get("test.bar"));
  }

  @Test
  public void testAppWithConfigSettingEqualsSyntax() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "0",
        "--exporter.fhir.export=false"};
    App.main(args);

    Assert.assertEquals(
        "Config should accept --key=value syntax",
        "false", Config.get("exporter.fhir.export"));
  }

  // ---------------------------------------------------------------------------
  // CLI argument tests
  // ---------------------------------------------------------------------------

  @Test
  public void testLongHelpArg() throws Exception {
    String[] args = {"--help"};
    String output = captureSystemOutAndErr(() -> App.main(args));
    assertOutputContains(output, "Usage");
    assertOutputNotContains(output, "NullPointerException");
    assertOutputNotContains(output, "Running with options:");
  }

  @Test
  public void testShortHelpArg() throws Exception {
    String[] args = {"-h"};
    String output = captureSystemOutAndErr(() -> App.main(args));
    assertOutputContains(output, "Usage");
    assertOutputNotContains(output, "NullPointerException");
    assertOutputNotContains(output, "Running with options:");
  }

  @Test
  public void testInvalidArgs() throws Exception {
    String[] args = {"-s", "foo", "-p", "foo", testStateDefault, testTownDefault};
    String output = captureSystemOutAndErr(() -> App.main(args));
    assertOutputContains(output, "Usage");
    assertOutputNotContains(output, "Running with options:");
  }

  @Test
  public void testMissingArgs() throws Exception {
    TestHelper.exportOff();
    String[] args = {};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Location: Massachusetts");
  }

  @Test
  public void testNullArgs() throws Exception {
    App.main(null);
  }

  // ---------------------------------------------------------------------------
  // Population and seed tests
  // ---------------------------------------------------------------------------

  @Test
  public void testAppWithZeroPopulation() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "0", testStateDefault, testTownDefault};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Seed:");
    assertOutputContains(output, "alive=0");
    assertOutputContains(output, "dead=0");
  }

  @Test
  public void testAppWithNegativeSeed() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "-1", "-p", "1", testStateDefault, testTownDefault};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "alive=1");
  }

  @Test
  public void testAppWithSinglePopulation() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "42", "-p", "1", testStateDefault, testTownDefault};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "alive=1");
    assertOutputContains(output, "Seed: 42");
  }

  @Test
  public void testAppWithZeroSeed() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "2", testStateDefault, testTownDefault};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Seed: 0");
    assertOutputContains(output, "alive=2");
  }

  @Test
  public void testAppWithLargePopulation() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "100", testStateDefault, testTownDefault};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Population: 100");
    assertOutputContains(output, "alive=100");
  }

  // ---------------------------------------------------------------------------
  // Gender filter tests
  // ---------------------------------------------------------------------------

  @Test
  public void testAppWithFemaleGender() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "3", "-g", "F"};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Gender: F");
    assertOutputContains(output, "alive=3");
    assertOutputNotContains(output, "y/o M");
  }

  @Test
  public void testAppWithInvalidGender() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "3", "-g", "X"};
    String output = captureSystemOutAndErr(() -> App.main(args));
    assertOutputContains(output, "Usage");
  }

  // ---------------------------------------------------------------------------
  // Combined filter tests
  // ---------------------------------------------------------------------------

  @Test
  public void testAppWithGenderAndAgeFilter() throws Exception {
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "5", "-g", "M", "-a", "40-50"};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Gender: M");
    assertOutputContains(output, "alive=5");
    assertOutputNotContains(output, "y/o F");
    String regex = "(.\n)*(4[0-9] y/o|50 y/o)(.\n)*";
    Assert.assertTrue(
        "Expected output to contain at least one person aged 40-50",
        Pattern.compile(regex).matcher(output).find());
  }

  @Test
  public void testAppWithGenderAgeAndLocation() throws Exception {
    PayerManager.clear();
    PayerManager.loadPayers(new Location(testStateAlternative, testTownAlternative));
    TestHelper.exportOff();
    String[] args = {"-s", "0", "-p", "2", "-g", "F", "-a", "20-30",
        testStateAlternative, testTownAlternative};
    String output = captureSystemOut(() -> App.main(args));
    assertOutputContains(output, "Running with options:");
    assertOutputContains(output, "Gender: F");
    assertOutputContains(output, "alive=2");
    String locationString = "Location: " + testTownAlternative + ", " + testStateAlternative;
    assertOutputContains(output, locationString);
    assertOutputNotContains(output, "y/o M");
  }
}
