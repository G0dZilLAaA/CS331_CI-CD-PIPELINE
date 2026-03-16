const dashboard = ()=>{
    console.log('dashboardRoutes');
}
app.post("/run-pipeline", async (req, res) => {

    const status = await triggerPipeline();

    if (status === 204) {
        res.json({ message: "Pipeline triggered successfully" });
    } else {
        res.json({ message: "Failed to trigger pipeline" });
    }
});