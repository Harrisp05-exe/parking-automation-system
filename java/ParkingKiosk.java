import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.UUID;

/** Java 17+ desktop entry kiosk. No external Java dependencies. */
public class ParkingKiosk extends JFrame {
    private final JTextField owner = new JTextField(), plate = new JTextField(), model = new JTextField(), color = new JTextField();
    private final JButton submit = new JButton("Assign my parking space  →"), reopen = new JButton("Open my parking pass"), next = new JButton("Next vehicle");
    private final JTextArea status = new JTextArea("Entry time is recorded automatically. Press Enter when you're ready.");
    private final String base = System.getenv().getOrDefault("PARKING_SERVER_URL", "http://127.0.0.1:8000").replaceAll("/+$", "");
    private final String key = System.getenv().getOrDefault("KIOSK_API_KEY", "local-kiosk-key");
    private String requestId = UUID.randomUUID().toString(), lastPayload = "";
    private URI pass;
    public ParkingKiosk() {
        super("Parkflow | Vehicle check-in");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        JPanel panel = new JPanel(); panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBorder(new EmptyBorder(30, 40, 30, 40)); panel.setBackground(new Color(246,249,246));
        JLabel brand = new JLabel("P  parkflow"); brand.setFont(new Font("SansSerif",Font.BOLD,28)); brand.setForeground(new Color(17,110,85)); panel.add(brand);
        panel.add(Box.createVerticalStrut(20)); JLabel title = new JLabel("Let's find your space."); title.setFont(new Font("SansSerif",Font.BOLD,22)); panel.add(title);
        field(panel, "Driver name", owner); field(panel, "Vehicle number plate", plate); field(panel, "Car make / model", model); field(panel, "Car color", color);
        panel.add(Box.createVerticalStrut(22)); submit.setBackground(new Color(17,110,85)); submit.setForeground(Color.BLACK); submit.setAlignmentX(Component.LEFT_ALIGNMENT); panel.add(submit);
        status.setEditable(false); status.setLineWrap(true); status.setWrapStyleWord(true); status.setOpaque(false); status.setBorder(new EmptyBorder(18,0,12,0)); status.setAlignmentX(Component.LEFT_ALIGNMENT); panel.add(status);
        reopen.setAlignmentX(Component.LEFT_ALIGNMENT); next.setAlignmentX(Component.LEFT_ALIGNMENT); reopen.setVisible(false); next.setVisible(false); panel.add(reopen); panel.add(Box.createVerticalStrut(10)); panel.add(next);
        submit.addActionListener(e -> checkIn()); reopen.addActionListener(e -> openPass()); next.addActionListener(e -> reset());
        getRootPane().setDefaultButton(submit); setContentPane(panel); setSize(520,700); setMinimumSize(new Dimension(450,650)); setLocationRelativeTo(null);
    }
    private void field(JPanel panel, String label, JTextField input) {
        panel.add(Box.createVerticalStrut(17)); JLabel text = new JLabel(label); text.setLabelFor(input); panel.add(text); panel.add(Box.createVerticalStrut(5));
        input.setMaximumSize(new Dimension(Integer.MAX_VALUE,38)); input.setFont(new Font("SansSerif",Font.PLAIN,16)); input.setAlignmentX(Component.LEFT_ALIGNMENT); panel.add(input);
    }
    private static String enc(String value) {return URLEncoder.encode(value.trim(),StandardCharsets.UTF_8);}
    static String errorMessage(Throwable error, String server) {
        Throwable cause = error;
        while (cause instanceof java.util.concurrent.ExecutionException && cause.getCause() != null) cause = cause.getCause();
        for (Throwable nested = cause; nested != null; nested = nested.getCause()) {
            if (nested instanceof java.net.http.HttpTimeoutException)
                return "Server timed out at " + server + ". Check that Django is running, then retry with the same details.";
            if (nested instanceof java.net.ConnectException || nested instanceof java.net.UnknownHostException || nested instanceof java.nio.channels.UnresolvedAddressException)
                return "Cannot connect to " + server + ". Start Django and ensure PARKING_SERVER_URL matches its address. Keep the server terminal open.";
            if (nested instanceof javax.net.ssl.SSLException)
                return "HTTPS connection failed. Check the server URL and its TLS certificate.";
        }
        String message = cause.getMessage();
        return message == null || message.isBlank() ? cause.getClass().getSimpleName() + ": check your server connection and configuration." : message;
    }
    private void checkIn() {
        if (!submit.isEnabled()) return;
        if (owner.getText().isBlank() || plate.getText().isBlank() || model.getText().isBlank() || color.getText().isBlank()) {status.setText("Please fill in all four fields."); return;}
        URI server;
        try {server = URI.create(base); if (server.getHost() == null || !(server.getScheme().equals("https") || (server.getScheme().equals("http") && (server.getHost().equals("127.0.0.1") || server.getHost().equals("localhost"))))) throw new IllegalArgumentException();}
        catch (Exception e) {status.setText("Set PARKING_SERVER_URL to an HTTPS address or local http://127.0.0.1:8000."); return;}
        String payload = "owner="+enc(owner.getText())+"&plate="+enc(plate.getText())+"&car_model="+enc(model.getText())+"&color="+enc(color.getText());
        if (!payload.equals(lastPayload)) {requestId = UUID.randomUUID().toString(); lastPayload = payload;}
        final String body = payload+"&request_id="+requestId;
        submit.setEnabled(false); for(JTextField f:new JTextField[]{owner,plate,model,color}) f.setEditable(false); status.setText("Finding an available space…");
        new SwingWorker<String,Void>() {
            protected String doInBackground() throws Exception {
                HttpRequest request = HttpRequest.newBuilder(URI.create(base+"/api/check-in/")).timeout(Duration.ofSeconds(30)).header("X-Kiosk-Key",key).header("Content-Type","application/x-www-form-urlencoded").POST(HttpRequest.BodyPublishers.ofString(body)).build();
                HttpResponse<String> response = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(15)).build().send(request,HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() != 200 && response.statusCode() != 201) throw new Exception(response.statusCode() == 400 || response.statusCode() == 403 || response.statusCode() == 409 || response.statusCode() == 503 ? response.body() : "Server returned HTTP "+response.statusCode()+". Check server configuration.");
                if (!response.body().matches("/visit/[0-9a-fA-F-]{36}/")) throw new Exception("Unexpected response from the server.");
                return base+response.body();
            }
            protected void done() {
                try {pass=URI.create(get()); reopen.setVisible(true); next.setVisible(true); for(JTextField f:new JTextField[]{owner,plate,model,color}) f.setEditable(false); status.setText("Space assigned! Your private parking pass:\n"+pass); openPass();}
                catch (Exception e) {status.setText("Check-in failed: "+errorMessage(e, base)+"\nYou can retry safely with the same details."); submit.setEnabled(true); for(JTextField f:new JTextField[]{owner,plate,model,color}) f.setEditable(true);}
            }
        }.execute();
    }
    private void openPass() {try {Desktop.getDesktop().browse(pass);} catch(Exception e) {status.setText("Space assigned. Copy this private URL into your browser:\n"+pass);}}
    private void reset() {for(JTextField f:new JTextField[]{owner,plate,model,color}) {f.setText(""); f.setEditable(true);} requestId=UUID.randomUUID().toString(); lastPayload=""; pass=null; submit.setEnabled(true); reopen.setVisible(false); next.setVisible(false); status.setText("Ready for the next vehicle."); owner.requestFocusInWindow();}
    public static void main(String[] args) {SwingUtilities.invokeLater(() -> {try {UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());} catch(Exception ignored) {} new ParkingKiosk().setVisible(true);});}
}
