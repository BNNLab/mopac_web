import streamlit as st
import subprocess
import os
import tempfile
import zipfile
import io

st.title("MOPAC-Web")
st.write("For when one only need to test a job and can't be bothered to install MOPAC or WebMO.")
st.write(
    "Upload MOPAC input files to run molecular modeling jobs. "
    "Choose single-job mode for one `.mop` file or batch mode to process many at once."
)

mode = st.radio("Select job type:", ["Single Job", "Batch Job"])

# ---------------------------------------------------------
# SINGLE JOB MODE
# ---------------------------------------------------------
if mode == "Single Job":
    st.header("Single MOPAC Job")
    uploaded_file = st.file_uploader("Upload a `.mop` input file", type=["mop"])

    if uploaded_file is not None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, uploaded_file.name)

            # Save file
            with open(input_path, "wb") as f:
                f.write(uploaded_file.read())

            base_name = os.path.splitext(uploaded_file.name)[0]
            out_file = os.path.join(temp_dir, f"{base_name}.out")
            aux_file = os.path.join(temp_dir, f"{base_name}.aux")

            if st.button("Run MOPAC"):
                with st.spinner("Running MOPAC..."):
                    try:
                        # Run MOPAC
                        cmd = ["mopac", input_path]
                        with open(out_file, "w") as out_f:
                            subprocess.run(
                                cmd, stdout=out_f, stderr=subprocess.STDOUT, check=True
                            )

                        # Bundle outputs into ZIP
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                            if os.path.exists(out_file):
                                zipf.write(out_file, arcname=f"{base_name}.out")
                            if os.path.exists(aux_file):
                                zipf.write(aux_file, arcname=f"{base_name}.aux")

                        zip_buffer.seek(0)

                        st.success("MOPAC completed!")

                        st.download_button(
                            label="Download Results (ZIP)",
                            data=zip_buffer,
                            file_name=f"{base_name}_results.zip",
                            mime="application/zip"
                        )

                    except subprocess.CalledProcessError:
                        st.error("MOPAC failed. Check the input file.")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")

# ---------------------------------------------------------
# BATCH JOB MODE
# ---------------------------------------------------------
elif mode == "Batch Job":
    st.header("Batch MOPAC Jobs")
    uploaded_zip = st.file_uploader("Upload a ZIP containing `.mop` files", type=["zip"])

    if uploaded_zip is not None:
        if st.button("Run Batch MOPAC"):
            with st.spinner("Running batch MOPAC jobs..."):
                try:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Save uploaded ZIP
                        zip_path = os.path.join(temp_dir, "inputs.zip")
                        with open(zip_path, "wb") as f:
                            f.write(uploaded_zip.read())

                        # Extract ZIP contents
                        with zipfile.ZipFile(zip_path, "r") as zip_in:
                            zip_in.extractall(temp_dir)

                        # Collect all .mop files
                        mop_files = [
                            f for f in os.listdir(temp_dir)
                            if f.lower().endswith(".mop")
                        ]
                        total_files = len(mop_files)

                        if total_files == 0:
                            st.error("No `.mop` files found in the ZIP.")
                            st.stop()

                        # Progress indicators
                        progress = st.progress(0)
                        status = st.empty()

                        # Prepare output ZIP
                        output_zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:

                            for i, filename in enumerate(mop_files):
                                mop_path = os.path.join(temp_dir, filename)
                                base = os.path.splitext(filename)[0]
                                out_file = os.path.join(temp_dir, f"{base}.out")
                                aux_file = os.path.join(temp_dir, f"{base}.aux")

                                status.text(f"Running MOPAC on {filename} ({i+1}/{total_files})...")

                                # Run MOPAC
                                cmd = ["mopac", mop_path]
                                with open(out_file, "w") as out_f:
                                    subprocess.run(
                                        cmd,
                                        stdout=out_f,
                                        stderr=subprocess.STDOUT,
                                        check=True
                                    )

                                # Add result files to output ZIP
                                if os.path.exists(out_file):
                                    zip_out.write(out_file, arcname=f"{base}.out")
                                if os.path.exists(aux_file):
                                    zip_out.write(aux_file, arcname=f"{base}.aux")

                                # Update progress bar
                                progress.progress((i + 1) / total_files)

                        output_zip_buffer.seek(0)
                        st.success("Batch MOPAC jobs completed!")

                        st.download_button(
                            label="Download All Results (ZIP)",
                            data=output_zip_buffer,
                            file_name="mopac_batch_results.zip",
                            mime="application/zip"
                        )

                except subprocess.CalledProcessError:
                    st.error("One or more MOPAC jobs failed.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
# =========================
# Sidebar controls
# =========================
st.sidebar.image("images/BNNLab_v3.png")
st.sidebar.header("Acknowledgements")
st.sidebar.write("This web tool was built to test MOPAC input files. MOPAC is an open-source molecule modelling package which employs molecular mechanics and semi-empirical methods.")
st.sidebar.header("Disclaimer")
st.sidebar.write("This software was developed by BNNLab, with all rights reserved. It is offered 'as is', without warranty of any kind, express or implied. The user assumes all risk for any malfunctions, errors, or damages resulting from the use of this software. The creator is not responsible for any direct or indirect loss arising from its use.")