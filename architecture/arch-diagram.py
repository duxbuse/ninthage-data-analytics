from diagrams import Cluster, Diagram, Edge
from diagrams.gcp.analytics import BigQuery, Dataflow
from diagrams.gcp.compute import Functions
from diagrams.gcp.devtools import Scheduler, Build, Tasks
from diagrams.gcp.storage import GCS
from diagrams.onprem.network import Internet
from diagrams.onprem.client import Users
from diagrams.onprem.analytics import Tableau
from diagrams.onprem.vcs import Github

diag_graph_attr = {
    "fontsize": "45",
}

node_attr = {
    "fontsize": "14",
}

gcp_attr = {
    "bgcolor": "#88C2CE",
}

discord_attr = {
    "bgcolor": "#5865F2"
}

core_attr = {
    "bgcolor": "#D6DFE8"
}

new_recruit_attr = {
    "bgcolor": "#ffe7b4"
}

with Diagram("ninthage-data-analytics architecture", show=False, graph_attr=diag_graph_attr, node_attr=node_attr,direction="TB"):
    """pylint: disable=unused-argument"""

    

    with Cluster("Google Cloud Platform - GCP", graph_attr=gcp_attr):
        with Cluster("Cloud build", graph_attr=core_attr):
            cloud_build = Build("Cloud Build")
            build_functions = Tasks("Build and deploy all\nWorkflows + Functions")

        # Static Data 
        static_bucket = GCS("bucket\n9th_builder_static_data")
        function_static_data = Functions("function\nstatic_data") 

        # Manual/TK flow
        tournament_lists = GCS("bucket\ntournament-lists")
        function_data_ingestion = Functions("function\ndata_ingestion")

        with Cluster("", graph_attr=core_attr):
            workflow_parse_lists = Dataflow("workflow\nparse_lists")
            function_data_conversion = Functions("function\ndata_conversion")
            tournament_lists_json = GCS("bucket\ntournament-lists-json")

        with Cluster("", graph_attr=core_attr):
            function_data_upload_data_into_bigquery = Functions("function\nupload data\ninto bigquery")

        # Cloud Scheduler
        scheduler = Scheduler("chron job 1/month")

        # Fading Flame
        function_data_fading_flame = Functions("function\ndata_fading_flame")
        fading_flame_bucket = GCS("bucket\nfading-flame")

        # Warhall
        function_warhall_report = Functions("function\ndata_warhall")
        warhall_bucket = GCS("bucket\nwarhall")

        # New Recruit
        function_new_recruit_tournaments = Functions("function\nnew_recruit\ntournaments")
        newrecruit_tournaments_bucket = GCS("bucket\nnewrecruit\ntournaments")

        # Manual Reports
        function_game_report = Functions("function\ngame_report")
        manual_game_reports_bucket = GCS("bucket\nmanual-game-reports")

        with Cluster("Discord Reporting", graph_attr=discord_attr):
            function_data_succcess_reporting = Functions("function\ndiscord\nsucccess\nreporting")
            function_data_failure_reporting = Functions("function\ndiscord\nfailure\nreporting")


        with Cluster("Big Query", graph_attr=core_attr):
            BQ_static_data = BigQuery("9th_builder_static_data")
            BQ_list_data = BigQuery("list_data")



        with Cluster("Discord Bot", graph_attr=discord_attr):
            discord_command_upload = Functions("function\ndiscord_bot\nupload.py")
            discord_command_static = Functions("function\ndiscord_bot\nstatic_data.py")

    with Cluster("Discord", graph_attr=discord_attr):
        discord_client = Users("Discord Client")


    with Cluster("9th Builder API", graph_attr=new_recruit_attr):
        builder_DataAnalytics = Internet("api/data_analytics/* ")
        builder_format = Internet("api/format")

    with Cluster("Visualizations", graph_attr=core_attr):
        tableau_client = Tableau("Tableau Client")

    with Cluster("Warhall", graph_attr=core_attr):
        warhall = Internet("Warhall")

    with Cluster("Fading Flame", graph_attr=core_attr):
        fading_flame = Internet("Fading Flame")

    with Cluster("Github", graph_attr=core_attr):
        manual_report = Github("Github Pages")
        repo = Github("Repository")

    with Cluster("New Recruit", graph_attr=new_recruit_attr):
        newrecruit_tournaments = Internet("api/tournaments")



    # Edges  -------------------------------------------------------------------------------------------------------

    # Static Flow      
    discord_client >> discord_command_static >> function_static_data >> builder_DataAnalytics >> function_static_data >> static_bucket >> BQ_static_data

    # Manual/TK Flow
    discord_client >> discord_command_upload >> function_data_ingestion >> tournament_lists >> workflow_parse_lists
    
    # Core workflow
    workflow_parse_lists >> function_data_conversion >> builder_format >> function_data_conversion >> tournament_lists_json >> function_data_upload_data_into_bigquery >> BQ_list_data
   
    # Workflow success/failure reporting
    workflow_parse_lists \
        >> Edge(color="darkgreen") \
        >> function_data_succcess_reporting >> discord_client
    workflow_parse_lists \
        >> Edge(color="red") \
        >> function_data_failure_reporting >> discord_client
        
    # Tableau
    BQ_list_data >> tableau_client
    BQ_static_data >> tableau_client

    # Fading Flame
    scheduler >> function_data_fading_flame >> fading_flame >> function_data_fading_flame >> fading_flame_bucket >> workflow_parse_lists

    # Warhall
    warhall >> function_warhall_report >> warhall_bucket >> workflow_parse_lists

    # Manual Reports
    manual_report >> function_game_report >> manual_game_reports_bucket >> workflow_parse_lists

    # New Recruit tournaments
    scheduler >> function_new_recruit_tournaments >> newrecruit_tournaments >> function_new_recruit_tournaments >> newrecruit_tournaments_bucket >> workflow_parse_lists

    # Cloud Build
    repo >> cloud_build >> build_functions