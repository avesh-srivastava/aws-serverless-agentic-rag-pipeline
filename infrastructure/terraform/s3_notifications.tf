# S3 Event Notifications
# Configure S3 to trigger Lambda functions on file uploads

# Lambda permission for S3 to invoke the ingestion trigger function
resource "aws_lambda_permission" "s3_invoke_ingestion_trigger" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = "aai_trigger_step_function_ingestion"
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw_data.arn

  # This resource depends on the Lambda function being deployed
  depends_on = [aws_s3_bucket.raw_data]
}

# S3 bucket notification configuration
resource "aws_s3_bucket_notification" "raw_data_notification" {
  bucket = aws_s3_bucket.raw_data.id

  lambda_function {
    lambda_function_arn = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:aai_trigger_step_function_ingestion"
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = ""
    filter_suffix       = ""
  }

  depends_on = [aws_lambda_permission.s3_invoke_ingestion_trigger]
}